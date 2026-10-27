"""Cargas agendadas: a agenda (beat) lida da configuração, as tarefas sobre o banco de teste (sem fila), a trava que
impede duas cargas ao mesmo tempo e o "Atualizar agora" do admin."""

from datetime import date

import pytest
from sqlalchemy import text

from app.core.config import Settings
from app.tasks.agenda import agenda_das_cargas, horario_do_cron
from app.tasks.cargas import (
    atualizacao_agora,
    carga_de_planilhas,
    carga_do_metryx,
    metryx_ligado,
    recalculo_do_estoque,
)
from app.tasks.trava import carga_rodando, trava_das_cargas
from tests.conftest import criar_usuario
from tests.sinteticos import gerar_planilha


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
    configuracao = Settings(agenda_planilhas="0 */2 * * *", agenda_metryx="", agenda_estoque="30 0 1 * *")
    agenda = agenda_das_cargas(configuracao)
    assert {nome: item["task"] for nome, item in agenda.items()} == {"planilhas": "cargas.planilhas",
                                                                       "estoque": "cargas.estoque"}


def test_carga_de_planilhas_e_a_segunda_passada_sem_mudanca(engine_etl, tmp_path):
    gerar_planilha(tmp_path)
    primeira = carga_de_planilhas(engine_etl, str(tmp_path), estabilidade_s=0)
    assert primeira["status"] in ("concluido", "concluido_com_avisos")
    assert sum(primeira["unidades"].values()) == 1
    # o arquivo não mudou: a próxima passada da agenda não recarrega
    assert carga_de_planilhas(engine_etl, str(tmp_path), estabilidade_s=0)["unidades"] == {"inalterada": 1}
    with engine_etl.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM core.fazenda")) == 1


def test_carga_recem_salva_espera_a_proxima_passada(engine_etl, tmp_path):
    gerar_planilha(tmp_path)
    resultado = carga_de_planilhas(engine_etl, str(tmp_path), estabilidade_s=3600)
    assert resultado["unidades"] == {}


def test_carga_sem_pasta_nao_faz_nada(engine_etl):
    assert carga_de_planilhas(engine_etl, None) == {"status": "sem_pasta"}


def test_uma_carga_por_vez(engine_etl, tmp_path):
    gerar_planilha(tmp_path)
    with trava_das_cargas(engine_etl, esperar=False) as conseguiu:
        assert conseguiu
        assert carga_de_planilhas(engine_etl, str(tmp_path), estabilidade_s=0) == {"status": "ocupada"}
        assert carga_do_metryx(engine_etl) == {"status": "ocupada"}
    # soltou: a carga roda
    assert carga_de_planilhas(engine_etl, str(tmp_path), estabilidade_s=0)["status"] != "ocupada"


def test_metryx_sem_credencial_nao_chama_a_api(engine_etl):
    resultado = carga_do_metryx(engine_etl)
    assert resultado["unidades"] == {}


def test_recalculo_do_estoque_estende_ate_o_mes(engine_etl, tmp_path):
    gerar_planilha(tmp_path)
    carga_de_planilhas(engine_etl, str(tmp_path), estabilidade_s=0)
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
    assert not metryx_ligado(Settings(agenda_metryx=""))
    assert not metryx_ligado(Settings(agenda_metryx="   "))
    assert metryx_ligado(Settings(agenda_metryx="0 6 * * *"))


def test_atualizar_agora_carrega_e_guarda_quem_pediu(engine_etl, engine_super, tmp_path):
    admin_id = criar_usuario(engine_super, "admin@terra.test", admin=True)
    gerar_planilha(tmp_path)
    resultado = atualizacao_agora(engine_etl, str(tmp_path), com_metryx=True, usuario_id=admin_id, estabilidade_s=0)
    assert resultado["planilhas"]["status"] in ("concluido", "concluido_com_avisos")
    assert resultado["metryx"]["unidades"] == {}                 # ligado, mas sem credencial: não chama a API
    with engine_etl.connect() as c:
        donos = c.execute(text("SELECT fonte, usuario_id FROM ingest.job ORDER BY iniciado_em")).all()
    assert [(fonte, dono) for fonte, dono in donos] == [("planilha", admin_id), ("metryx", admin_id)]


def test_atualizar_agora_sem_metryx_e_sem_pasta(engine_etl):
    assert atualizacao_agora(engine_etl, None, com_metryx=False) == {"planilhas": {"status": "sem_pasta"}}


def test_atualizar_agora_espera_a_vez(engine_etl, tmp_path):
    gerar_planilha(tmp_path)
    with trava_das_cargas(engine_etl, esperar=False):
        assert atualizacao_agora(engine_etl, str(tmp_path), com_metryx=False) == {"status": "ocupada"}
