"""Cargas agendadas: a agenda (beat) lida da configuração, as tarefas sobre o banco de teste (sem fila), a trava que
impede duas cargas ao mesmo tempo e o "Atualizar agora" do admin (só o Metryx: as planilhas chegam pela tela)."""

from datetime import date

import pytest
from sqlalchemy import text

from app.core.config import Settings
from app.etl.adapters.planilha.adapter import AdapterPlanilha
from app.etl.pipeline import MotorCarga
from app.tasks.agenda import agenda_das_cargas, horario_do_cron
from app.tasks.cargas import (
    atualizacao_agora,
    carga_do_metryx,
    importacoes_na_fila,
    recalculo_do_estoque,
)
from app.tasks.trava import carga_rodando, trava_das_cargas
from tests.conftest import criar_usuario
from tests.sinteticos import gerar_planilha

METRYX_LIGADO = Settings(agenda_metryx="0 6 * * *")
METRYX_DESLIGADO = Settings(agenda_metryx="")


def test_horario_do_cron():
    a_cada_duas_horas = horario_do_cron("0 */2 * * *")
    assert (sorted(a_cada_duas_horas.minute), sorted(a_cada_duas_horas.hour)) == ([0], list(range(0, 24, 2)))
    dia_primeiro = horario_do_cron("30 0 1 * *")
    assert (sorted(dia_primeiro.day_of_month), sorted(dia_primeiro.minute)) == ([1], [30])
    assert horario_do_cron("") is None
    assert horario_do_cron("   ") is None
    with pytest.raises(ValueError, match="agenda inválida"):
        horario_do_cron("0 2 *")


def test_agenda_tem_so_as_cargas_com_horario():
    configuracao = Settings(agenda_importacoes="*/5 * * * *", agenda_metryx="", agenda_estoque="30 0 1 * *")
    agenda = agenda_das_cargas(configuracao)
    assert {nome: item["task"] for nome, item in agenda.items()} == {"importacoes": "cargas.importacoes",
                                                                       "estoque": "cargas.estoque"}
    # as planilhas não têm agenda (chegam pela tela); o Metryx entra quando a agenda dele é preenchida
    com_o_metryx = agenda_das_cargas(METRYX_LIGADO)
    assert sorted(com_o_metryx) == ["estoque", "importacoes", "metryx"]


def test_uma_carga_por_vez(engine_etl):
    with trava_das_cargas(engine_etl, esperar=False) as conseguiu:
        assert conseguiu
        assert importacoes_na_fila(engine_etl) == {"status": "ocupada"}
        assert carga_do_metryx(engine_etl) == {"status": "ocupada"}
        assert atualizacao_agora(engine_etl, METRYX_LIGADO) == {"status": "ocupada"}
    # soltou: a carga roda
    assert carga_do_metryx(engine_etl)["status"] != "ocupada"


def test_metryx_sem_credencial_nao_chama_a_api(engine_etl):
    resultado = carga_do_metryx(engine_etl)
    assert resultado["unidades"] == {}


def test_recalculo_do_estoque_estende_ate_o_mes(engine_etl, tmp_path):
    gerar_planilha(tmp_path)
    MotorCarga(engine_etl).executar(AdapterPlanilha(tmp_path))
    assert recalculo_do_estoque(engine_etl, date(2025, 12, 15))["status"] == "concluido"
    with engine_etl.connect() as c:
        ultimo_mes = c.scalar(text("SELECT max(competencia) FROM fato.estoque_mensal"))
    assert ultimo_mes == date(2025, 12, 1)


def test_a_trava_aparece_para_quem_olha_de_fora(engine_etl, engine_api):
    with engine_api.connect() as outra_conexao:
        assert not carga_rodando(outra_conexao)
        with trava_das_cargas(engine_etl, esperar=False):
            assert carga_rodando(outra_conexao)
        assert not carga_rodando(outra_conexao)


def test_metryx_so_entra_no_atualizar_agora_com_a_agenda_ligada():
    assert not METRYX_DESLIGADO.metryx_ligado
    assert not Settings(agenda_metryx="   ").metryx_ligado
    assert METRYX_LIGADO.metryx_ligado


def test_atualizar_agora_sincroniza_o_metryx_e_guarda_quem_pediu(engine_etl, engine_super):
    admin_id = criar_usuario(engine_super, "admin@terra.test", admin=True)
    resultado = atualizacao_agora(engine_etl, METRYX_LIGADO, usuario_id=admin_id)
    assert resultado["unidades"] == {}                           # ligado, mas sem credencial: não chama a API
    with engine_etl.connect() as c:
        donos = c.execute(text("SELECT fonte, usuario_id FROM ingest.job ORDER BY iniciado_em")).all()
    assert [(fonte, dono) for fonte, dono in donos] == [("metryx", admin_id)]


def test_atualizar_agora_com_o_metryx_desligado_nao_faz_nada(engine_etl):
    assert atualizacao_agora(engine_etl, METRYX_DESLIGADO) == {"status": "metryx_desligado"}
    with engine_etl.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM ingest.job")) == 0
