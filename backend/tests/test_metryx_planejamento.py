"""Planejamento do Metryx (cenário planejado): versão escolhida, metas de animais, rebanho médio pela evolução do
rebanho e DRE previsto. Regras em app/etl/adapters/metryx/planejamento.py."""

from datetime import date
from decimal import Decimal

from sqlalchemy import text

from app.etl.adapters.metryx import credenciais
from app.etl.adapters.metryx.adapter import AdapterMetryx
from app.etl.adapters.metryx.normalizar import normalizar
from app.etl.adapters.metryx.planejamento import Evolucao, mes_do_item
from app.etl.pipeline import MotorCarga
from tests.sinteticos import (
    CLIENTE,
    FAZENDA,
    FAZENDA_2,
    fluxo_de_caixa,
    item_do_plano,
    payloads_metryx,
    plano_metryx,
    previsao_financeira,
    transporte_metryx,
)
from tests.test_metryx import cliente, conteudo_bruto

FAZENDA_EXTERNA = f"{CLIENTE}|{FAZENDA}"


def lote_do_plano(**plano):
    return normalizar(conteudo_bruto(payloads_metryx(**plano)))


def planejados(lote, tipo: str) -> list:
    return [mov for mov in lote.mov_animal if mov.cenario == "planejado" and mov.tipo == tipo]


def avisos(lote, codigo: str) -> list[str]:
    return [ocorrencia.mensagem for ocorrencia in lote.ocorrencias if ocorrencia.codigo == codigo]


# --- versão do plano -------------------------------------------------------------------------------------------------

def test_metas_entram_de_todas_as_versoes_com_numero_e_nome():
    """As telas escolhem a versão (o BI soma todas, e as metas dobram): a carga guarda cada uma com o número, que dá a
    ordem, e o nome; oficial marca a mais recente, que vale quando ninguém escolhe outra."""
    nascimentos = [item_do_plano("7/25", 11, 100, versao=1), item_do_plano("7/25", 11, 80, versao=3)]
    lote = lote_do_plano(nascimento_plano=nascimentos)
    metas = sorted((mov.versao_plano, mov.qtd) for mov in planejados(lote, "NASCIMENTO"))
    assert metas == [(f"{FAZENDA_EXTERNA}|v1", 100), (f"{FAZENDA_EXTERNA}|v3", 80)]
    versoes = [(versao.codigo, versao.nome, versao.ordem, versao.oficial) for versao in lote.versoes]
    assert versoes == [(f"{FAZENDA_EXTERNA}|v1", "Versão 1", 1, False), (f"{FAZENDA_EXTERNA}|v3", "Versão 3", 3, True)]
    assert avisos(lote, "PLAN_VERSION_CHOSEN") == [
        "plano com mais de uma versão na safra; todas entram, e sem escolha na tela vale a mais recente: "
        "Fazenda Metryx 25-26: versão 3 (Versão 3) (outras: versão 1 (Versão 1))"]


def test_versao_e_escolhida_por_fazenda_e_safra():
    """O número da versão é da fazenda (cada uma tem a sua versão 1) e a escolha é por safra."""
    nascimentos = [item_do_plano("7/25", 11, 100, versao=1),
                   item_do_plano("7/26", 11, 90, versao=2, safra="26-27"),
                   item_do_plano("7/25", 11, 50, versao=1, fazenda=FAZENDA_2)]
    lote = lote_do_plano(nascimento_plano=nascimentos)
    metas = sorted((mov.fazenda, mov.data, mov.qtd, mov.versao_plano) for mov in planejados(lote, "NASCIMENTO"))
    assert metas == [(FAZENDA_EXTERNA, date(2025, 7, 1), 100, f"{FAZENDA_EXTERNA}|v1"),
                     (FAZENDA_EXTERNA, date(2026, 7, 1), 90, f"{FAZENDA_EXTERNA}|v2"),
                     (f"{CLIENTE}|{FAZENDA_2}", date(2025, 7, 1), 50, f"{CLIENTE}|{FAZENDA_2}|v1")]
    assert avisos(lote, "PLAN_VERSION_CHOSEN") == []


def test_versao_antiga_de_outro_endpoint_tambem_entra():
    """A versão nova só com nascimentos não apaga as mortes da antiga: quem escolhe a versão é a tela (com a mais
    recente, a safra fica sem meta de mortes, porque as metas vêm de um plano só; tests/test_versao_do_plano.py)."""
    lote = lote_do_plano(nascimento_plano=[item_do_plano("7/25", 11, 80, versao=2)],
                         morte_plano=[item_do_plano("7/25", 11, 3, versao=1)])
    assert [mov.versao_plano for mov in planejados(lote, "NASCIMENTO")] == [f"{FAZENDA_EXTERNA}|v2"]
    assert [mov.versao_plano for mov in planejados(lote, "MORTE")] == [f"{FAZENDA_EXTERNA}|v1"]


# --- metas de animais ------------------------------------------------------------------------------------------------

def test_venda_e_compra_previstas_viram_totais():
    """`weight` é por cabeça e `totalValue` é o total; a carcaça do abate é weight × yield/100 por cabeça."""
    abate = item_do_plano("8/25", 7, 10, type="Abate", weight=480.0, arrobaValue=300.0, totalValue=51840.0)
    abate["yield"] = 54.0                          # `yield` é palavra reservada: não dá para passar como argumento
    em_pe = item_do_plano("9/25", 12, 5, type="Em Pé", weight=300.0, totalValue=15000.0)
    compra = item_do_plano("8/25", 12, 1200, weight=220.0, totalValue=2345496.0)
    lote = lote_do_plano(venda_plano=[abate, em_pe], compra_plano=[compra])
    vendas = {mov.tipo: (mov.qtd, mov.peso_vivo_total_kg, mov.peso_carcaca_total_kg, mov.valor_total)
              for mov in lote.mov_animal if mov.cenario == "planejado" and mov.tipo != "COMPRA"}
    assert vendas == {"ABATE": (10, Decimal("4800.0"), Decimal("2592.00"), Decimal("51840.0")),
                      "VENDA_EM_PE": (5, Decimal("1500.0"), None, Decimal("15000.0"))}
    [comprada] = planejados(lote, "COMPRA")
    assert (comprada.qtd, comprada.peso_vivo_total_kg, comprada.valor_total) == (1200, 264000, Decimal("2345496.0"))


def test_desmame_previsto_e_categorias_do_plano():
    """O planejamento tem catálogo próprio (de-para 'metryx_plano'), com a sugestão de categoria BI."""
    desmame = item_do_plano("6/25", 11, 300)
    for campo in ("idCategory", "categoryName", "animalGroupName", "age", "gender"):
        del desmame[campo]
    desmame |= {"oldCategoryId": 11, "oldCategoryName": "Bezerro 00 a 08 Meses", "oldAnimalGroupName":
                "Bezerros Mamando", "oldAge": "00-08", "oldGender": "Macho", "newCategoryId": 12, "newCategoryName":
                "Garrote 08 a 12 Meses", "newAnimalGroupName": "Garrotes e Bois", "newAge": "08-12", "newGender": "Macho"}
    lote = lote_do_plano(desmame_plano=[desmame])
    [mov] = planejados(lote, "DESMAME")
    assert (mov.categoria.id_externo, mov.categoria_destino.id_externo, mov.qtd) == ("11", "12", 300)
    do_plano = {(c.chave.id_externo, c.nome, c.categoria_bi) for c in lote.categorias
                if c.chave.fonte_mapa == "metryx_plano"}
    assert do_plano == {("11", "Bezerro 00 a 08 Meses", "BEZERRO"), ("12", "Garrote 08 a 12 Meses", "MACHOS 8-12")}


def test_meta_sem_versao_vai_para_a_quarentena():
    sem_versao = item_do_plano("7/25", 11, 100)
    sem_versao["plVersionCode"] = None
    lote = lote_do_plano(nascimento_plano=[sem_versao])
    assert planejados(lote, "NASCIMENTO") == []
    do_plano = [(r.entidade, r.codigo) for r in lote.rejeitadas if r.origem_linha.startswith("nascimento_plano")]
    assert do_plano == [("mov_animal", "REQUIRED_MISSING")]


# --- rebanho médio previsto ------------------------------------------------------------------------------------------

def test_evolucao_da_o_saldo_do_fim_do_mes_sem_pular_mes_parado():
    """O rebanho previsto do mês é o saldo do fim do mês, como o relatório financeiro do Metryx (U6, 10/11/2026)."""
    evolucao = Evolucao()
    evolucao.somar_saldo_inicial("8", Decimal(50))
    evolucao.somar_movimento(date(2025, 7, 1), "8", Decimal(10))
    evolucao.somar_movimento(date(2025, 9, 1), "8", Decimal(-10))
    assert evolucao.saldos_do_fim_do_mes() == {(date(2025, 7, 1), "8"): 60, (date(2025, 8, 1), "8"): 60,
                                               (date(2025, 9, 1), "8"): 50}


def test_rebanho_medio_previsto_pela_evolucao_e_categoria_negativa_conta_zero():
    """Plano que desmama bezerros que a evolução não tem (U6): a categoria fica negativa (o total fecha) e conta zero
    no rebanho médio, com aviso. A saída pode vir com a quantidade negativa."""
    evolucao = [item_do_plano(None, 12, 100, type="Entrada", originMovement="Saldo Inicial"),
                item_do_plano("7/25", 12, 20, type="Entrada", originMovement="Desmame Entrada"),
                item_do_plano("7/25", 11, -20, type="Saída", originMovement="Desmame Saída"),
                item_do_plano("8/25", 12, 10, type="Saída", originMovement="Morte")]
    lote = lote_do_plano(rebanho_plano=evolucao)
    medias = {(r.categoria.id_externo, r.competencia): r.qtd_cab for r in lote.rebanho_medio
              if r.cenario == "planejado"}
    assert medias == {("12", date(2025, 7, 1)): 120, ("12", date(2025, 8, 1)): 110}
    assert avisos(lote, "PLAN_NEGATIVE_STOCK") == [
        "a evolução do plano deixa categorias negativas em alguns meses; elas contam zero no rebanho médio previsto "
        "(cab·mês que ficaram de fora: Fazenda Metryx: 40)"]
    assert lote.rejeitadas == []


# --- DRE previsto ----------------------------------------------------------------------------------------------------

def test_dre_previsto_natureza_pelo_sinal_numa_versao_propria():
    previsao = [previsao_financeira("2025-07-01", -1500, "Débito"),
                previsao_financeira("2025-08-01", 3000, "Crédito", centro="Rebanho\u200b", subcentro="Venda"),
                previsao_financeira("2025-09-01", 0, "Débito")]
    lote = lote_do_plano(previsao_financeiro=previsao)
    orcado = [(o.competencia, o.conta.centro, o.natureza, o.valor, o.versao_plano) for o in lote.orcamentos]
    assert orcado == [(date(2025, 7, 1), "Pastagens", "D", 1500, "previsao-financeiro"),
                      (date(2025, 8, 1), "Rebanho", "C", 3000, "previsao-financeiro")]
    assert [versao.codigo for versao in lote.versoes] == ["previsao-financeiro"]


# --- partições e carga -----------------------------------------------------------------------------------------------

def test_particoes_do_planejado_so_dos_endpoints_que_vieram():
    conteudo = conteudo_bruto(payloads_metryx(**plano_metryx()))
    conteudo["endpoints"]["compra_plano"] = "proibido"
    lote = normalizar(conteudo)
    assert lote.validar_contrato() == []
    do_plano = set()
    for particao in lote.particoes:
        if particao.cenario == "planejado" and particao.fazenda == FAZENDA_EXTERNA:
            do_plano.add((particao.entidade, particao.tipos))
    assert do_plano == {("mov_animal", ("NASCIMENTO",)), ("rebanho_medio", None), ("orcamento", ("previsao",))}
    assert all(p.versao_plano is None for p in lote.particoes)    # vale para todas as versões da fazenda


def carregar(engine_etl, dados):
    adapter = AdapterMetryx(engine_etl, cliente(transporte_metryx(dados)))
    return MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(adapter)


def previsto(engine_super) -> dict:
    with engine_super.connect() as c:
        return {
            "nascimentos": c.execute(text("SELECT sum(qtd) FROM fato.mov_animal "
                                          "WHERE cenario = 'planejado' AND tipo = 'NASCIMENTO'")).scalar(),
            "versoes": c.execute(text("SELECT array_agg(DISTINCT v.codigo ORDER BY v.codigo) FROM fato.mov_animal m "
                                      "JOIN dim.versao_plano v ON v.id = m.versao_plano_id")).scalar(),
            "rebanho": c.execute(text("SELECT sum(qtd_cab) FROM fato.rebanho_medio_mensal "
                                      "WHERE cenario = 'planejado'")).scalar(),
            "orcado": c.execute(text("SELECT sum(valor) FROM fato.orcamento_financeiro")).scalar(),
        }


def test_carga_do_planejado_com_versao_nova_e_versao_apagada(engine_etl, engine_super):
    """A versão nova entra ao lado da anterior (a tela escolhe). A partição vale para todas as versões: a versão que
    o Metryx deixou de mostrar sai do banco na carga seguinte."""
    credenciais.registrar(engine_etl, CLIENTE, "token-teste", "Cliente Teste")
    r = carregar(engine_etl, payloads_metryx(**plano_metryx()))
    assert r.unidades[0].status.startswith("carregada"), r.unidades[0].erro
    assert previsto(engine_super) == {"nascimentos": 100, "versoes": [f"{FAZENDA_EXTERNA}|v1"], "rebanho": 110,
                                      "orcado": 1500}
    plano = plano_metryx()
    plano["nascimento_plano"].append(item_do_plano("7/25", 11, 90, versao=2))
    plano["rebanho_plano"] += [item_do_plano(None, 11, 200, versao=2, type="Entrada", originMovement="Saldo Inicial"),
                               item_do_plano("7/25", 11, 10, versao=2, type="Entrada", originMovement="nascimento")]
    carregar(engine_etl, payloads_metryx(**plano))
    assert previsto(engine_super) == {"nascimentos": 190, "versoes": [f"{FAZENDA_EXTERNA}|v1", f"{FAZENDA_EXTERNA}|v2"],
                                      "rebanho": 320, "orcado": 1500}
    so_a_versao_2 = plano_metryx()
    so_a_versao_2["nascimento_plano"] = [item_do_plano("7/25", 11, 90, versao=2)]
    so_a_versao_2["rebanho_plano"] = plano["rebanho_plano"][2:]
    carregar(engine_etl, payloads_metryx(**so_a_versao_2))
    assert previsto(engine_super) == {"nascimentos": 90, "versoes": [f"{FAZENDA_EXTERNA}|v2"], "rebanho": 210,
                                      "orcado": 1500}


# --- o mês das metas ------------------------------------------------------------------------------------------------

def test_mes_das_metas_sai_do_month_e_da_safra():
    """A API escreve junho com o ano do início da safra ("6/25" na 25-26), mas junho é o último mês dela."""
    assert mes_do_item(item_do_plano("7/25", 12, 1)) == date(2025, 7, 1)
    assert mes_do_item(item_do_plano("12/25", 12, 1)) == date(2025, 12, 1)
    assert mes_do_item(item_do_plano("1/26", 12, 1)) == date(2026, 1, 1)
    assert mes_do_item(item_do_plano("5/26", 12, 1)) == date(2026, 5, 1)
    assert mes_do_item(item_do_plano("6/25", 12, 1)) == date(2026, 6, 1)
    assert mes_do_item(item_do_plano("6/26", 12, 1, safra="26-27")) == date(2027, 6, 1)


def test_sem_month_ou_com_safra_estranha_fica_o_date():
    sem_month = item_do_plano("6/25", 12, 1)
    del sem_month["month"]
    assert mes_do_item(sem_month) == date(2025, 6, 1)
    outra_safra = item_do_plano("6/25", 12, 1, safra="2025")
    outra_safra["harvest"] = "2025"
    assert mes_do_item(outra_safra) == date(2025, 6, 1)
    assert mes_do_item(item_do_plano(None, 12, 1)) is None      # saldo inicial: month 0, sem data


def test_meta_de_junho_entra_no_fim_da_safra():
    lote = lote_do_plano(nascimento_plano=[item_do_plano("6/25", 11, 40)])
    assert [mov.data for mov in planejados(lote, "NASCIMENTO")] == [date(2026, 6, 1)]


def test_evolucao_com_o_desmame_de_junho_depois_dos_nascimentos():
    """Serra Dourada 25/26: nascem em julho e desmamam em junho. Com o junho da API ("6/25") no começo da safra, o
    desmame vinha antes dos nascimentos e a categoria ficava negativa."""
    evolucao = [item_do_plano(None, 12, 50, type="Entrada", originMovement="Saldo Inicial"),
                item_do_plano("7/25", 11, 100, type="Entrada", originMovement="Nascimento"),
                item_do_plano("6/25", 11, -100, type="Saída", originMovement="Desmame Saída"),
                item_do_plano("6/25", 12, 100, type="Entrada", originMovement="Desmame Entrada")]
    lote = lote_do_plano(rebanho_plano=evolucao)
    medias = {(r.categoria.id_externo, r.competencia): r.qtd_cab for r in lote.rebanho_medio
              if r.cenario == "planejado"}
    assert medias[("11", date(2025, 7, 1))] == 100 and medias[("11", date(2026, 5, 1))] == 100
    assert ("11", date(2026, 6, 1)) not in medias and medias[("12", date(2026, 6, 1))] == 150
    assert avisos(lote, "PLAN_NEGATIVE_STOCK") == []


# --- orçamento do planejamento (fluxo de caixa, por versão) ----------------------------------------------------------

def test_fluxo_de_caixa_entra_com_todas_as_versoes():
    """O orçamento do planejamento entra de todas as versões (a tela escolhe qual comparar), com a natureza do `type`
    e no centro de custo quando o subcentro é o genérico; a previsão financeira continua como orçamento à parte."""
    fluxo = [fluxo_de_caixa("2025-07-01", 1000, "Débito", versao=1),
             fluxo_de_caixa("2025-07-01", 1200, "Débito", versao=3),
             fluxo_de_caixa("2025-07-01", 5000, "Crédito", versao=3, centro="Rebanho", subcentro="Venda de Rebanho")]
    lote = lote_do_plano(**plano_metryx(), fluxo_caixa_plano=fluxo)
    assert lote.validar_contrato() == []
    do_planejamento = set()
    for orcamento in lote.orcamentos:
        if orcamento.tipo == "planejamento":
            do_planejamento.add((orcamento.versao_plano.split("|")[-1], orcamento.natureza, orcamento.conta.centro,
                                 orcamento.conta.subcentro, orcamento.valor))
    assert do_planejamento == {("v1", "D", "Pastagens", None, Decimal(1000)),
                               ("v3", "D", "Pastagens", None, Decimal(1200)),
                               ("v3", "C", "Rebanho", "Venda de Rebanho", Decimal(5000))}
    assert [orcamento.valor for orcamento in lote.orcamentos if orcamento.tipo == "previsao"] == [Decimal(1500)]
    versoes = {versao.codigo: (versao.oficial, versao.ordem) for versao in lote.versoes}
    # a versão 1 é a das metas de animais (a mais recente delas); a 3 só tem orçamento
    assert versoes[f"{FAZENDA_EXTERNA}|v1"] == (True, 1) and versoes[f"{FAZENDA_EXTERNA}|v3"] == (False, 3)
    tipos = {particao.tipos for particao in lote.particoes if particao.entidade == "orcamento"}
    assert tipos == {("previsao",), ("planejamento",)}


def test_despesa_do_fluxo_de_caixa_com_valor_negativo_continua_debito():
    """U6 26/27: os projetos do plano vêm com `type` "Débito" e o valor negativo ("Contrapiso curral (MO)", −20.000). É
    a convenção de saída do Metryx, e não estorno: antes a natureza invertia e a despesa virava crédito, e o desembolso
    previsto da safra ficava negativo."""
    fluxo = [fluxo_de_caixa("2025-07-01", -20000, "Débito", versao=1),
             fluxo_de_caixa("2025-07-01", 1000, "Débito", versao=1),
             fluxo_de_caixa("2025-07-01", 5000, "Crédito", versao=1, centro="Rebanho", subcentro="Venda de Rebanho")]
    lote = lote_do_plano(**plano_metryx(), fluxo_caixa_plano=fluxo)
    do_planejamento = sorted((orcamento.natureza, orcamento.valor) for orcamento in lote.orcamentos
                             if orcamento.tipo == "planejamento")
    assert do_planejamento == [("C", Decimal(5000)), ("D", Decimal(1000)), ("D", Decimal(20000))]


def test_fluxo_de_caixa_sem_natureza_vai_para_a_quarentena():
    lote = lote_do_plano(fluxo_caixa_plano=[fluxo_de_caixa("2025-07-01", 1000, "Transferência", versao=1)])
    assert not [orcamento for orcamento in lote.orcamentos if orcamento.tipo == "planejamento"]
    assert [rejeitada.codigo for rejeitada in lote.rejeitadas] == ["REQUIRED_MISSING"]
