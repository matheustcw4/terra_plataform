"""Tela de integrações (só admin): as APIs que alimentam o painel e o histórico das cargas de cada uma, cliente por
cliente, com os erros e os avisos agrupados. As cargas usam o adapter em memória com a fonte "metryx"."""

from datetime import date

from sqlalchemy import text

from app.core.config import Settings
from app.etl.pipeline import MotorCarga
from app.services import integracoes
from tests.fabrica import AdapterMemoria, exemplo_doc01
from tests.test_api import entrar, usuario_com_senha

CARGAS = "/api/v1/admin/integracoes/metryx/cargas"


class AdapterSemLista(AdapterMemoria):
    """A fonte nem lista as unidades, como com a METRYX_CHAVE_CIFRA errada (os tokens não decifram)."""

    def descobrir(self):
        raise RuntimeError("token não decifra com a METRYX_CHAVE_CIFRA atual")


def motor(engine_etl) -> MotorCarga:
    return MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1))


def test_agenda_em_palavras():
    assert integracoes.agenda_em_palavras("0 3 * * *") == "todo dia às 03:00, horário de Cuiabá"
    assert integracoes.agenda_em_palavras("30 14 * * *") == "todo dia às 14:30, horário de Cuiabá"
    assert integracoes.agenda_em_palavras("") == "desligada"
    assert integracoes.agenda_em_palavras("0 6 * * 1-5") == "no horário do cron 0 6 * * 1-5 (Cuiabá)"


def test_a_api_ligada_e_a_da_agenda_preenchida():
    [ligada] = integracoes.listar(Settings(agenda_metryx="0 3 * * *"))
    assert (ligada.fonte, ligada.rotulo, ligada.ligada, ligada.variavel_da_agenda) == ("metryx", "Metryx", True,
                                                                                       "AGENDA_METRYX")
    [desligada] = integracoes.listar(Settings(agenda_metryx=""))
    assert (desligada.ligada, desligada.quando) == (False, "desligada")


def test_a_carga_que_nem_lista_as_unidades_fecha_com_o_erro(engine_etl, engine_super):
    resultado = motor(engine_etl).executar(AdapterSemLista("metryx", {}))
    assert resultado.status == "erro"
    with engine_super.connect() as c:
        job = c.execute(text("SELECT status, finalizado_em FROM ingest.job")).one()
        mensagem = c.scalar(text("SELECT mensagem FROM ingest.ocorrencia WHERE codigo = 'EXTRACT_FAILED'"))
    assert job.status == "erro"
    assert job.finalizado_em is not None                  # antes ficava "processando" para sempre
    assert "não decifra" in mensagem


def test_historico_mostra_cada_cliente_e_os_avisos(api, engine_etl, engine_super):
    admin_id = usuario_com_senha(engine_super, "admin@terra.test", admin=True)
    admin = entrar(api, "admin@terra.test")
    lotes = {"metryx:a": exemplo_doc01("metryx"),
             "metryx:b": exemplo_doc01("metryx", cliente="2", fazenda="2|X", nome_fazenda="X")}
    motor(engine_etl).executar(AdapterMemoria("metryx", lotes, falhar_extracao={"metryx:b"}))
    motor(engine_etl).executar(AdapterSemLista("metryx", {}), usuario_id=admin_id)

    resposta = api.get(CARGAS, headers=admin)
    assert resposta.status_code == 200, resposta.text
    falhou, anterior = resposta.json()
    # a mais recente primeiro: a que nem listou os clientes, pedida pelo admin
    assert (falhou["status"], falhou["pedida_por"], falhou["unidades"]) == ("erro", "admin@terra.test", [])
    assert [(aviso["codigo"], aviso["problema"]) for aviso in falhou["avisos"]] == [
        ("EXTRACT_FAILED", "Não deu para buscar os dados")]
    assert "não decifra" in falhou["avisos"][0]["exemplo"]
    # a anterior: um cliente carregou e o outro não (o motivo vem junto); a agenda pediu (sem usuário)
    assert (anterior["status"], anterior["pedida_por"]) == ("concluido_com_avisos", None)
    por_nome = {unidade["nome"]: unidade for unidade in anterior["unidades"]}
    assert por_nome["metryx:a"]["status"].startswith("carregada")
    assert por_nome["metryx:b"]["status"] == "erro"
    assert "não consegui ler" in por_nome["metryx:b"]["erro"]
    assert anterior["avisos"][0]["nivel"] == "erro"       # os erros vêm antes dos avisos


def test_so_o_admin_ve_as_integracoes(api, engine_super):
    usuario_com_senha(engine_super, "consultor@terra.test")
    consultor = entrar(api, "consultor@terra.test")
    assert api.get("/api/v1/admin/integracoes", headers=consultor).status_code == 403
    assert api.get(CARGAS, headers=consultor).status_code == 403
    usuario_com_senha(engine_super, "admin@terra.test", admin=True)
    admin = entrar(api, "admin@terra.test")
    assert [api_integrada["fonte"] for api_integrada in api.get("/api/v1/admin/integracoes", headers=admin).json()] == [
        "metryx"]
    assert api.get("/api/v1/admin/integracoes/planilha/cargas", headers=admin).status_code == 404
