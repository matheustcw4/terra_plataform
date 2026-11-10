"""A versão do planejamento nas páginas com meta (regras em app/kpis/versao_do_plano.py).

Fazenda Metryx sintética, safra 25/26, julho/2025:
- versão 1: 100 nascimentos e 3 mortes previstos; evolução do rebanho de 90 bezerros (+20 em julho);
- versão 2: 90 nascimentos e nenhuma morte; evolução de 200 bezerros (+10 em julho).
Numa fazenda e safra entra uma versão só: a mais recente (2) por padrão, e as mortes da versão 1 não entram.
"""

import uuid
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
    [da_fazenda] = plano["fazendas"]
    assert [versao["rotulo"] for versao in da_fazenda["versoes"]] == ["Versão 2", "Versão 1"]
    assert (da_fazenda["escolhidas"], da_fazenda["sem_plano"], plano["em_uso"]) == ([], False, ["Versão 2"])


def test_versao_escolhida_vale_nas_metas_de_todas_as_paginas(pedir):
    versao_1 = pedir("movimentacao")["plano"]["fazendas"][0]["versoes"][1]["id"]
    pagina = pedir("movimentacao", versao=versao_1)
    assert metas(pagina) == (100, 3)
    assert (pagina["plano"]["fazendas"][0]["escolhidas"], pagina["plano"]["em_uso"]) == ([versao_1], ["Versão 1"])
    nascimentos = pedir("nascimentos", versao=versao_1)
    assert nascimentos["quadro"][0]["planejado"] == 100 and nascimentos["plano"]["em_uso"] == ["Versão 1"]
    assert pedir("mortes", versao=versao_1)["quadro"][0]["planejado"] == 3


def test_a_funcao_do_banco_escolhe_por_fazenda_e_safra(engine_super, fazenda_metryx):
    """Rebanho médio previsto e metas seguem a mesma versão: a função olha os dois."""
    with engine_super.connect() as c:
        versoes = dict(c.execute(text("SELECT codigo, id FROM dim.versao_plano")).all())
        consulta = text("SELECT safra, versao_plano_id FROM app.versoes_do_planejado(CAST(:f AS uuid[]), "
                        "CAST(:v AS uuid[]), CAST(:s AS uuid[])) ORDER BY 2")
        fazendas = [str(fazenda_metryx)]
        padrao = c.execute(consulta, {"f": fazendas, "v": [], "s": []}).all()
        # a marcada de outra fazenda (aqui, um id qualquer) não atrapalha a escolha desta
        pedida = c.execute(consulta, {"f": fazendas, "v": [str(uuid.uuid4()), str(versoes[f"{CLIENTE}|{FAZENDA}|v1"])],
                                      "s": []}).all()
        do_plano = [versoes[f"{CLIENTE}|{FAZENDA}|v1"], versoes[f"{CLIENTE}|{FAZENDA}|v2"]]
        as_duas = c.execute(consulta, {"f": fazendas, "v": [str(versao) for versao in do_plano], "s": []}).all()
        sem_plano = c.execute(consulta, {"f": fazendas, "v": [], "s": fazendas}).all()
    assert padrao == [(2025, versoes[f"{CLIENTE}|{FAZENDA}|v2"])]
    assert pedida == [(2025, versoes[f"{CLIENTE}|{FAZENDA}|v1"])]
    assert sorted(as_duas) == sorted((2025, versao) for versao in do_plano)
    assert sem_plano == []


def test_versoes_marcadas_somam_e_sem_planejamento_zera_as_metas(pedir):
    """Pedido do usuário, 10/11/2026: seleção múltipla por fazenda (as marcadas somam: 100 + 90 nascimentos) e a opção
    "nenhum planejamento" (a fazenda fica sem meta, e a tela diz que nada está valendo)."""
    versoes = [versao["id"] for versao in pedir("movimentacao")["plano"]["fazendas"][0]["versoes"]]
    as_duas = pedir("movimentacao", versao=versoes)
    assert metas(as_duas) == (190, 3)
    assert sorted(as_duas["plano"]["fazendas"][0]["escolhidas"]) == sorted(versoes)
    assert as_duas["plano"]["em_uso"] == ["Versão 2", "Versão 1"]
    sem_plano = pedir("movimentacao", sem_plano=[str(pedir.fazenda)])
    assert metas(sem_plano) == (0, 0)
    assert (sem_plano["plano"]["fazendas"][0]["sem_plano"], sem_plano["plano"]["em_uso"]) == (True, [])


def test_o_menu_lista_as_versoes_de_cada_fazenda(pedir):
    """No MENU (pedido do usuário, 10/11/2026): a escolha é por fazenda, e a lista junta as versões das metas e as do
    orçamento do planejamento; todas as fazendas do filtro aparecem."""
    menu = pedir("versoes_do_plano")
    [da_fazenda] = menu["fazendas"]
    assert [versao["rotulo"] for versao in da_fazenda["versoes"]] == ["Versão 2", "Versão 1"]
    versao_1 = da_fazenda["versoes"][1]["id"]
    escolhida = pedir("versoes_do_plano", versao=versao_1)
    assert (escolhida["fazendas"][0]["escolhidas"], escolhida["em_uso"]) == ([versao_1], ["Versão 1"])


def test_uma_versao_so_nao_tem_o_que_escolher_mas_diz_qual_vale(api, engine_super, engine_etl):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    adapter = AdapterMetryx(engine_etl, cliente(transporte_metryx(payloads_metryx(**plano_metryx()))))
    MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(adapter)
    with engine_super.connect() as c:
        fazenda = c.execute(text("SELECT entidade_id FROM core.fonte_vinculo WHERE entidade = 'fazenda' "
                                 "AND id_externo = :e"), {"e": f"{CLIENTE}|{FAZENDA}"}).scalar_one()
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda])
    plano = Consultor(api, entrar(api, "consultor@terra.test"), fazenda)("movimentacao")["plano"]
    # a fazenda aparece com a única versão dela (a tela mostra o nome, sem lista para escolher)
    assert plano["em_uso"] == ["Versão 1"]
    assert [(da_fazenda["fazenda"], [versao["rotulo"] for versao in da_fazenda["versoes"]], da_fazenda["escolhidas"])
            for da_fazenda in plano["fazendas"]] == [("Fazenda Metryx", ["Versão 1"], [])]
