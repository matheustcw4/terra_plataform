"""O planejado do financeiro nas páginas Previsto × Realizado e Financeiro: a tela escolhe o orçamento (previsão
financeira ou planejamento) e a versão do plano (regras em app/kpis/previsto_financeiro.py).

Fazenda Metryx sintética, conta Pastagens, safra 25/26:
- previsão financeira: R$ 1.500 de débito em 07/2025;
- planejamento: versão 1 com R$ 1.000 em 07/2025 e R$ 300 em 08/2025; versão 3 com R$ 1.200 em 07/2025.
Numa fazenda e safra entra uma versão só: a mais recente (3) por padrão, sem somar o agosto da versão 1.
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.etl.adapters.metryx import credenciais
from app.etl.adapters.metryx.adapter import AdapterMetryx
from app.etl.pipeline import MotorCarga
from tests.sinteticos import CLIENTE, FAZENDA, fluxo_de_caixa, payloads_metryx, plano_metryx, transporte_metryx
from tests.test_api import entrar, usuario_com_senha
from tests.test_metryx import cliente

FLUXO = [fluxo_de_caixa("2025-07-01", 1000, "Débito", versao=1),
         fluxo_de_caixa("2025-08-01", 300, "Débito", versao=1),
         fluxo_de_caixa("2025-07-01", 1200, "Débito", versao=3)]


@pytest.fixture
def fazenda_metryx(engine_etl, engine_super):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    adapter = AdapterMetryx(engine_etl, cliente(transporte_metryx(payloads_metryx(**plano_metryx(),
                                                                                  fluxo_caixa_plano=FLUXO))))
    resultado = MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(adapter)
    assert resultado.unidades[0].status.startswith("carregada"), resultado.unidades[0].erro
    with engine_super.connect() as c:
        return c.execute(text("SELECT entidade_id FROM core.fonte_vinculo WHERE entidade = 'fazenda' "
                              "AND id_externo = :e"), {"e": f"{CLIENTE}|{FAZENDA}"}).scalar_one()


class Consultor:
    """Pede as páginas da fazenda Metryx como um consultor com acesso a ela (RLS de verdade)."""

    def __init__(self, api: TestClient, cabecalhos: dict, fazenda):
        self.api = api
        self.cabecalhos = cabecalhos
        self.fazenda = fazenda

    def __call__(self, pagina: str, **escolha) -> dict:
        parametros = {"fazendas": [str(self.fazenda)], "inicio": "2025-07", "fim": "2025-09", **escolha}
        resposta = self.api.get(f"/api/v1/dashboards/{pagina}", headers=self.cabecalhos, params=parametros)
        assert resposta.status_code == 200, resposta.text
        return resposta.json()


@pytest.fixture
def pedir(api: TestClient, engine_super, fazenda_metryx) -> Consultor:
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda_metryx])
    return Consultor(api, entrar(api, "consultor@terra.test"), fazenda_metryx)


def planejado_de_pastagens(pagina: dict) -> float:
    for grupo in pagina["grupos"]:
        for conta in grupo["contas"]:
            if conta["nome"] == "Pastagens":
                return conta["acumulado"]["planejado"]
    raise AssertionError("conta Pastagens fora da matriz")


def test_sem_escolha_vale_a_previsao_financeira_e_a_tela_recebe_as_opcoes(pedir):
    pagina = pedir("previsto_realizado")
    assert planejado_de_pastagens(pagina) == 1500
    previsto = pagina["previsto"]
    assert [tipo["codigo"] for tipo in previsto["tipos"]] == ["previsao", "planejamento"]
    # a previsão financeira tem uma versão só: não há versão para escolher
    assert (previsto["tipo"], previsto["versao"], previsto["versoes"]) == ("previsao", None, [])


def test_planejamento_usa_a_versao_mais_recente_da_safra(pedir):
    pagina = pedir("previsto_realizado", previsto="planejamento")
    assert planejado_de_pastagens(pagina) == 1200          # o agosto da versão 1 não soma com a versão 3
    assert [versao["rotulo"] for versao in pagina["previsto"]["versoes"]] == ["Versão 3", "Versão 1"]
    assert pagina["previsto"]["versao"] is None


def test_versao_escolhida_substitui_a_mais_recente(pedir):
    versoes = pedir("previsto_realizado", previsto="planejamento")
    versao_1 = versoes["previsto"]["versoes"][1]["id"]
    pagina = pedir("previsto_realizado", previsto="planejamento", versao=versao_1)
    assert planejado_de_pastagens(pagina) == 1300
    assert pagina["previsto"]["versao"] == versao_1


def desembolso_planejado(pagina: dict) -> list[float]:
    return [mes["desembolso_planejado"] for mes in pagina["serie_mensal"]]


def test_financeiro_segue_a_mesma_escolha(pedir):
    assert desembolso_planejado(pedir("financeiro")) == [1500, 0, 0]
    planejamento = pedir("financeiro", previsto="planejamento")
    assert desembolso_planejado(planejamento) == [1200, 0, 0]
    versao_1 = planejamento["previsto"]["versoes"][1]["id"]
    assert desembolso_planejado(pedir("financeiro", previsto="planejamento", versao=versao_1)) == [1000, 300, 0]
