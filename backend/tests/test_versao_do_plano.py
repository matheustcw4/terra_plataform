"""A versão do planejamento nas páginas com meta (regras em app/kpis/versao_do_plano.py).

Fazenda Metryx sintética, safra 25/26, julho/2025:
- versão 1: 100 nascimentos e 3 mortes previstos; evolução do rebanho de 100 bezerros (+20 em julho);
- versão 2: 90 nascimentos e nenhuma morte; evolução de 200 bezerros (+10 em julho).
Numa fazenda e safra entra uma versão só: a mais recente (2) por padrão, e as mortes da versão 1 não entram.
"""

from datetime import date

import pytest
from sqlalchemy import text

from app.etl.adapters.metryx import credenciais
from app.etl.adapters.metryx.adapter import AdapterMetryx
from app.etl.pipeline import MotorCarga
from tests.sinteticos import CLIENTE, FAZENDA, item_do_plano, payloads_metryx, plano_metryx, transporte_metryx
from tests.test_api import entrar, usuario_com_senha
from tests.test_metryx import cliente
from tests.test_previsto_financeiro import Consultor


def plano_com_duas_versoes() -> dict:
    plano = plano_metryx()
    plano["nascimento_plano"].append(item_do_plano("7/25", 11, 90, versao=2))
    plano["morte_plano"] = [item_do_plano("7/25", 11, 3, versao=1)]
    plano["rebanho_plano"] += [item_do_plano(None, 11, 200, versao=2, type="Entrada", originMovement="Saldo Inicial"),
                               item_do_plano("7/25", 11, 10, versao=2, type="Entrada", originMovement="nascimento")]
    return plano


@pytest.fixture
def fazenda_metryx(engine_etl, engine_super):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    adapter = AdapterMetryx(engine_etl, cliente(transporte_metryx(payloads_metryx(**plano_com_duas_versoes()))))
    resultado = MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(adapter)
    assert resultado.unidades[0].status.startswith("carregada"), resultado.unidades[0].erro
    with engine_super.connect() as c:
        return c.execute(text("SELECT entidade_id FROM core.fonte_vinculo WHERE entidade = 'fazenda' "
                              "AND id_externo = :e"), {"e": f"{CLIENTE}|{FAZENDA}"}).scalar_one()


@pytest.fixture
def pedir(api, engine_super, fazenda_metryx) -> Consultor:
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda_metryx])
    return Consultor(api, entrar(api, "consultor@terra.test"), fazenda_metryx)


def metas(pagina: dict) -> tuple[float, float]:
    return pagina["nascimentos"]["planejado"], pagina["mortes"]["planejado"]


def test_sem_escolha_vale_a_versao_mais_recente_em_todas_as_metas(pedir):
    pagina = pedir("movimentacao")
    assert metas(pagina) == (90, 0)                 # as mortes da versão 1 não entram na safra da versão 2
    plano = pagina["plano"]
    assert [versao["rotulo"] for versao in plano["versoes"]] == ["Versão 2", "Versão 1"]
    assert (plano["versao"], plano["em_uso"]) == (None, ["Versão 2"])


def test_versao_escolhida_vale_nas_metas_de_todas_as_paginas(pedir):
    versao_1 = pedir("movimentacao")["plano"]["versoes"][1]["id"]
    pagina = pedir("movimentacao", versao=versao_1)
    assert metas(pagina) == (100, 3)
    assert (pagina["plano"]["versao"], pagina["plano"]["em_uso"]) == (versao_1, ["Versão 1"])
    nascimentos = pedir("nascimentos", versao=versao_1)
    assert nascimentos["quadro"][0]["planejado"] == 100 and nascimentos["plano"]["em_uso"] == ["Versão 1"]
    assert pedir("mortes", versao=versao_1)["quadro"][0]["planejado"] == 3


def test_a_funcao_do_banco_escolhe_por_fazenda_e_safra(engine_super, fazenda_metryx):
    """Rebanho médio previsto e metas seguem a mesma versão: a função olha os dois."""
    with engine_super.connect() as c:
        versoes = dict(c.execute(text("SELECT codigo, id FROM dim.versao_plano")).all())
        consulta = text("SELECT safra, versao_plano_id FROM app.versoes_do_planejado(CAST(:f AS uuid[]), :v)")
        padrao = c.execute(consulta, {"f": [str(fazenda_metryx)], "v": None}).all()
        pedida = c.execute(consulta, {"f": [str(fazenda_metryx)], "v": versoes[f"{CLIENTE}|{FAZENDA}|v1"]}).all()
    assert padrao == [(2025, versoes[f"{CLIENTE}|{FAZENDA}|v2"])]
    assert pedida == [(2025, versoes[f"{CLIENTE}|{FAZENDA}|v1"])]


def test_uma_versao_so_nao_tem_o_que_escolher_mas_diz_qual_vale(api, engine_super, engine_etl):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    adapter = AdapterMetryx(engine_etl, cliente(transporte_metryx(payloads_metryx(**plano_metryx()))))
    MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(adapter)
    with engine_super.connect() as c:
        fazenda = c.execute(text("SELECT entidade_id FROM core.fonte_vinculo WHERE entidade = 'fazenda' "
                                 "AND id_externo = :e"), {"e": f"{CLIENTE}|{FAZENDA}"}).scalar_one()
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda])
    plano = Consultor(api, entrar(api, "consultor@terra.test"), fazenda)("movimentacao")["plano"]
    assert plano == {"versoes": [], "versao": None, "em_uso": ["Versão 1"]}
