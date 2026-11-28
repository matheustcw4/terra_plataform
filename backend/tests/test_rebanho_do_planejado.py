"""O rebanho que divide o planejado do financeiro (desembolso e custeio por cabeça por mês) é o da mesma versão que deu o
dinheiro planejado, só nas fazendas que têm o orçamento (pedido do usuário, 27/11/2026; regra em
app/kpis/previsto_financeiro.py, VERSOES_DO_REBANHO_PREVISTO).

O caso da Maister, em miniatura (julho de 2025): a fazenda Metryx tem o plano (versão 1, rebanho previsto de 110
cabeças), o orçamento do planejamento (R$ 1.000 de adubação) e a previsão financeira (R$ 1.500, que não entra no
planejado desde 27/11/2026); a "Outra" tem só um
plano de rebanho (500 cabeças), sem orçamento nenhum, como o plano "Global (teste)" da Maister. No GRUPO, as 500 cabeças
dela não podem entrar no divisor.
"""

from datetime import date

import pytest
from sqlalchemy import text

from app.etl.adapters.metryx import credenciais
from app.etl.adapters.metryx.adapter import AdapterMetryx
from app.etl.pipeline import MotorCarga
from tests.sinteticos import (
    CLIENTE,
    FAZENDA,
    FAZENDA_2,
    fluxo_de_caixa,
    item_do_plano,
    payloads_metryx,
    plano_metryx,
    transporte_metryx,
)
from tests.test_api import entrar, usuario_com_senha
from tests.test_metryx import cliente


def plano_so_de_rebanho_na_outra_fazenda() -> list[dict]:
    """490 no saldo inicial e +10 em julho: 500 no fim do mês, sem orçamento."""
    return [item_do_plano(None, 11, 490, fazenda=FAZENDA_2, type="Entrada", originMovement="Saldo Inicial"),
            item_do_plano("7/25", 11, 10, fazenda=FAZENDA_2, type="Entrada", originMovement="nascimento")]


@pytest.fixture
def duas_fazendas(engine_etl, engine_super) -> list:
    plano = plano_metryx()
    plano["rebanho_plano"] = plano["rebanho_plano"] + plano_so_de_rebanho_na_outra_fazenda()
    dados = payloads_metryx(**plano, fluxo_caixa_plano=[fluxo_de_caixa("2025-07-01", 1000, "Débito", versao=1)])
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    resultado = MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(
        AdapterMetryx(engine_etl, cliente(transporte_metryx(dados))))
    assert resultado.unidades[0].status.startswith("carregada"), resultado.unidades[0].erro
    with engine_super.connect() as c:
        return list(c.execute(text("SELECT entidade_id FROM core.fonte_vinculo WHERE entidade = 'fazenda' "
                                   "AND id_externo IN (:a, :b)"),
                              {"a": f"{CLIENTE}|{FAZENDA}", "b": f"{CLIENTE}|{FAZENDA_2}"}).scalars())


def por_cabeca(api, cabecalhos, fazendas, previsto: str) -> float:
    resposta = api.get("/api/v1/dashboards/financeiro", headers=cabecalhos,
                       params={"fazendas": [str(f) for f in fazendas], "inicio": "2025-07", "fim": "2025-07",
                               "previsto": previsto})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()["desembolso_por_cabeca_mes"]["planejado"]


def test_o_rebanho_da_fazenda_sem_orcamento_nao_entra_no_divisor(api, engine_super, duas_fazendas):
    assert len(duas_fazendas) == 2
    with engine_super.connect() as c:          # a outra fazenda tem mesmo as 500 cabeças previstas em julho
        outra = c.scalar(text("SELECT sum(r.qtd_cab) FROM fato.rebanho_medio_mensal r JOIN core.fonte_vinculo v "
                              "ON v.entidade_id = r.fazenda_id WHERE v.id_externo = :f AND r.cenario = 'planejado' "
                              "AND r.competencia = '2025-07-01'"), {"f": f"{CLIENTE}|{FAZENDA_2}"})
    assert outra == 500
    usuario_com_senha(engine_super, "admin@terra.test", admin=True)
    admin = entrar(api, "admin@terra.test")
    # planejamento: R$ 1.000 ÷ 110 cabeças da versão do orçamento (antes, ÷ 610: as 500 da outra fazenda entravam)
    assert por_cabeca(api, admin, duas_fazendas, "planejamento") == pytest.approx(1000 / 110)
    # um link antigo que pede a previsão financeira dá o planejamento do mesmo jeito: ela não é planejado
    assert por_cabeca(api, admin, duas_fazendas, "previsao") == pytest.approx(1000 / 110)
