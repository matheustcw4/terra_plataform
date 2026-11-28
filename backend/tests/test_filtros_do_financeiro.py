"""Os filtros do financeiro (pedido do usuário, 18/11/2026): tipo de atividade, classificação e conta bancária, e a
classificação do Metryx valendo para os dados do Metryx (regras em app/kpis/filtros_do_financeiro.py e na migração
0029).

Fazenda Metryx sintética, julho de 2025, tudo pago:
- realizado: Pastagens R$ 1.000 (Pecuária Campo, Itaú), Pastagens R$ 400 (Agricultura Permanente, Banco do Brasil) e
  Financiamentos débitos R$ 300 (Financiamento, atividade sem tipo no de-para; Itaú). O lançamento não traz a
  classificação: ela vem do centro de custo no plano (Pastagens = Custeio; Financiamentos = Outros débitos);
- planejamento (versão 1, Pecuária): Pastagens R$ 1.200 (Custeio) e Financiamentos débitos R$ 100 (Outros débitos) e,
  em agosto, Manutenção da fazenda R$ 50 com uma classificação que o de-para não conhece (vale a da conta);
- previsão financeira: Pastagens R$ 1.500, que vem no payload e não entra no planejado (pedido do usuário, 27/11/2026).
"""

from datetime import date

import pytest
from sqlalchemy import text

from app.etl.adapters.metryx import credenciais
from app.etl.adapters.metryx.adapter import AdapterMetryx
from app.etl.adapters.metryx.normalizar import normalizar
from app.etl.canonical import ContaBancariaOrigem
from app.etl.pipeline import MotorCarga
from tests.sinteticos import CLIENTE, FAZENDA, fluxo_de_caixa, payloads_metryx, previsao_financeira, transporte_metryx
from tests.test_api import entrar, usuario_com_senha
from tests.test_metryx import cliente
from tests.test_previsto_financeiro import Consultor


def lancamento(numero: int, centro: str, subcentro: str, valor: float, atividade: str, conta: tuple[str, str]) -> dict:
    return {"idCustomer": CLIENTE, "idFarmFiscal": FAZENDA, "idfarmDestination": FAZENDA,
            "idFinancialEntrie": f"f{numero}", "idPayment": f"p{numero}", "parcel": "1", "costCenter": centro,
            "subCenter": subcentro, "type": "Débito", "amountPaid": valor, "datePayment": "2025-07-15",
            "dueDate": "2025-07-10", "activity": atividade, "idBankAccount": conta[0], "banckAccount": conta[1]}


ITAU = ("b1", "Itaú - SP")
BB = ("b2", "Banco do Brasil")
LANCAMENTOS = [lancamento(1, "Pastagens", "Adubação", 1000, "Pecuária Campo", ITAU),
               lancamento(2, "Pastagens", "Adubação", 400, "Agricultura Permanente", BB),
               lancamento(3, "Financiamentos débitos", "Juros", 300, "Financiamento", ITAU)]


def financiamento_no_plano() -> dict:
    item = fluxo_de_caixa("2025-07-01", 100, "Débito", versao=1, centro="Financiamentos débitos")
    item["classificationAnalyticDescription"] = "Outros débitos"
    item["classificationAnalyticDisbursement"] = False
    return item


def classe_nova_no_plano() -> dict:
    item = fluxo_de_caixa("2025-08-01", 50, "Débito", versao=1, centro="Manutenção da fazenda")
    item["classificationAnalyticDescription"] = "Classe Nova"
    item["classificationAnalyticDisbursement"] = False
    return item


def payload() -> dict:
    return payloads_metryx(
        lancamento=LANCAMENTOS,
        fluxo_caixa_plano=[fluxo_de_caixa("2025-07-01", 1200, "Débito", versao=1), financiamento_no_plano(),
                           classe_nova_no_plano()],
        previsao_financeiro=[previsao_financeira("2025-07-01", -1500, "Débito")])


@pytest.fixture
def fazenda_metryx(engine_etl, engine_super):
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    adapter = AdapterMetryx(engine_etl, cliente(transporte_metryx(payload())))
    resultado = MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(adapter)
    assert resultado.unidades[0].status.startswith("carregada"), resultado.unidades[0].erro
    with engine_super.connect() as c:
        return c.execute(text("SELECT entidade_id FROM core.fonte_vinculo WHERE entidade = 'fazenda' "
                              "AND id_externo = :e"), {"e": f"{CLIENTE}|{FAZENDA}"}).scalar_one()


@pytest.fixture
def pedir(api, engine_super, fazenda_metryx) -> Consultor:
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda_metryx])
    return Consultor(api, entrar(api, "consultor@terra.test"), fazenda_metryx)


def planejado_por_mes(pagina: dict) -> dict[str, float]:
    return {mes["mes"]: mes["desembolso_planejado"] for mes in pagina["serie_mensal"]}


def test_o_adapter_leva_a_atividade_a_conta_e_a_classificacao_do_centro():
    lote = normalizar({"idCustomer": CLIENTE, "endpoints": {}, "dados": payload()})
    pastagens, agricultura, financiamento = lote.lancamentos
    assert (pastagens.atividade, pastagens.conta_bancaria) == ("Pecuária Campo", ContaBancariaOrigem(
        id_externo="b1", nome="Itaú - SP"))
    assert (pastagens.classificacao.nome, pastagens.classificacao.desembolso) == ("Custeio", True)
    assert agricultura.atividade == "Agricultura Permanente"
    assert (financiamento.classificacao.nome, financiamento.classificacao.desembolso) == ("Outros débitos", False)
    assert {orcamento.tipo for orcamento in lote.orcamentos} == {"planejamento"}      # a previsão não entra
    assert {(item.atividade, item.classificacao.nome) for item in lote.orcamentos} == {
        ("Pecuária", "Custeio"), ("Pecuária", "Outros débitos"), ("Pecuária", "Classe Nova")}


def test_a_carga_grava_os_de_paras_e_avisa_o_que_esta_pendente(fazenda_metryx, engine_super):
    with engine_super.connect() as c:
        contas = c.execute(text("SELECT nome FROM dim.conta_bancaria ORDER BY nome")).scalars().all()
        pendente = c.scalar(text("SELECT tipo_atividade_id FROM dim.atividade_map WHERE nome_origem = 'Financiamento'"))
        nova = c.execute(text("SELECT classificacao, entra_desembolso FROM dim.classificacao_map "
                              "WHERE nome_origem = 'Classe Nova'")).one()
        avisos = set(c.execute(text("SELECT codigo FROM ingest.ocorrencia")).scalars())
    assert contas == ["Banco do Brasil", "Itaú - SP"]
    assert pendente is None                                   # o admin dá o tipo; até lá, "A classificar"
    assert tuple(nova) == (None, False)                       # sem grupo do DRE: as linhas usam a da conta
    assert {"ACTIVITY_UNCLASSIFIED", "CLASSIFICATION_UNMAPPED"} <= avisos


def test_a_classificacao_do_metryx_vale_sobre_a_marca_da_conta(fazenda_metryx, engine_super):
    """Financiamentos débitos: a dimensão põe no desembolso, e a exceção do Metryx (migração 0022), no custeio; a
    classificação do Metryx (Outros débitos, sem desembolso) tira dos dois."""
    with engine_super.connect() as c:
        linhas = c.execute(text("""
            SELECT centro_custo, classificacao, classificacao_analitica, entra_custeio, entra_desembolso,
                   tipo_atividade
            FROM fato.v_lancamento_financeiro ORDER BY valor DESC""")).all()
        manutencao = c.execute(text("SELECT classificacao_analitica, entra_desembolso FROM fato.v_orcamento_financeiro "
                                    "WHERE centro_custo = 'Manutenção da fazenda'")).one()
    assert [tuple(linha) for linha in linhas] == [
        ("Pastagens", "D - CUSTEIO", "Custeio", True, True, "Pecuária"),
        ("Pastagens", "D - CUSTEIO", "Custeio", True, True, "Agricultura"),
        ("Financiamentos débitos", "F - OUTROS DÉBITOS", "Outros débitos", False, False, "A classificar")]
    assert tuple(manutencao) == ("Custeio", True)            # classificação nova da fonte: vale a da conta


def test_sem_filtro_tudo_entra_e_o_financiamento_fica_fora_do_desembolso(pedir):
    pagina = pedir("financeiro")
    assert pagina["desembolso"] == 1400
    assert planejado_por_mes(pagina)["2025-07-01"] == 1200


def test_o_tipo_de_atividade_recorta_o_realizado_e_o_planejado(pedir):
    agricultura = pedir("financeiro", previsto="planejamento", atividade=["Agricultura"])
    assert agricultura["desembolso"] == 400
    assert planejado_por_mes(agricultura)["2025-07-01"] == 0      # o plano é todo de Pecuária
    pecuaria = pedir("financeiro", previsto="planejamento", atividade=["Pecuária"])
    assert pecuaria["desembolso"] == 1000
    assert planejado_por_mes(pecuaria)["2025-07-01"] == 1200
    assert pedir("financeiro", atividade=["Pecuária", "Agricultura"])["desembolso"] == 1400


def test_a_conta_bancaria_recorta_so_o_realizado(pedir, engine_super):
    with engine_super.connect() as c:
        banco_do_brasil = c.scalar(text("SELECT id FROM dim.conta_bancaria WHERE id_externo = 'b2'"))
    pagina = pedir("financeiro", conta=[str(banco_do_brasil)])
    assert pagina["desembolso"] == 400
    assert planejado_por_mes(pagina)["2025-07-01"] == 1200       # o plano não é vinculado a conta: fica inteiro


def test_a_classificacao_recorta_a_matriz_do_previsto(pedir):
    pagina = pedir("previsto_realizado", previsto="planejamento", classificacao=["Outros débitos"])
    grupos = {grupo["classificacao"]: grupo["total"]["acumulado"] for grupo in pagina["grupos"]}
    assert set(grupos) == {"F - OUTROS DÉBITOS"}
    assert (grupos["F - OUTROS DÉBITOS"]["realizado"], grupos["F - OUTROS DÉBITOS"]["planejado"]) == (300, 100)


def test_o_escopo_traz_as_opcoes_que_a_fazenda_tem(api, engine_super, fazenda_metryx):
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda_metryx])
    escopo = api.get("/api/v1/escopo", headers=entrar(api, "consultor@terra.test")).json()
    [capacidades] = [fazenda["capacidades"] for fazenda in escopo["fazendas"] if fazenda["id"] == str(fazenda_metryx)]
    assert capacidades["tipos_de_atividade"] == ["Pecuária", "Agricultura", "A classificar"]
    assert capacidades["classificacoes"] == ["Custeio", "Outros débitos"]
    assert [conta["nome"] for conta in capacidades["contas_bancarias"]] == ["Banco do Brasil", "Itaú - SP"]
    # a ordem geral, para a tela juntar as opções de várias fazendas
    assert escopo["opcoes_do_financeiro"] == {"tipos_de_atividade": capacidades["tipos_de_atividade"],
                                              "classificacoes": capacidades["classificacoes"]}


def test_o_admin_da_o_tipo_da_atividade_e_o_filtro_muda_na_hora(api, engine_super, pedir):
    usuario_com_senha(engine_super, "admin@terra.test", admin=True)
    admin = entrar(api, "admin@terra.test")
    lista = api.get("/api/v1/admin/atividades", headers=admin).json()
    assert [item["nome"] for item in lista["itens"]] == ["Financiamento"]          # só as pendentes, por padrão
    assert [opcao["nome"] for opcao in lista["opcoes"]] == ["Pecuária", "Agricultura", "Silvicultura",
                                                            "Outras atividades"]
    [financiamento] = lista["itens"]
    assert (financiamento["lancamentos"], financiamento["valor"]) == (1, 300)
    outras = lista["opcoes"][-1]["id"]
    caminho = f"/api/v1/admin/atividades/{financiamento['id']}"
    assert api.put(caminho, headers=admin, json={"tipo_atividade_id": outras}).status_code == 204
    try:
        pagina = pedir("previsto_realizado", atividade=["Outras atividades"])
        [grupo] = [grupo for grupo in pagina["grupos"] if grupo["classificacao"] == "F - OUTROS DÉBITOS"]
        assert grupo["total"]["acumulado"]["realizado"] == 300
    finally:
        assert api.put(caminho, headers=admin, json={"tipo_atividade_id": None}).status_code == 204
    assert api.get("/api/v1/admin/atividades", headers=pedir.cabecalhos).status_code == 403
