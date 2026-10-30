"""Boletim analítico (o "Exportar PDF" no modo Analítico), pela API e nas regras puras.

Fazenda sintética (tests/sinteticos.py): em jul/2025 nascem 120 bezerros e morrem 5 (Cobra) e há o desmame de 300;
em ago/2025 saem 10 vacas vendidas em pé (R$ 30.000, 4.500 kg); rebanho médio de jul/2025 = 1.550 cabeças, área de
1.000 ha. As metas: 32 nascimentos em julho e 2 mortes em julho.
"""

from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient

from app.kpis.analitico.comparar import comparado, linha_do_placar, status
from app.kpis.analitico.estoque import COLUNAS_DO_ESTOQUE, DoMes, leitura_do_estoque, lotacao_prevista
from app.kpis.analitico.financeiro import frase_do_resultado, leitura_financeira
from app.kpis.analitico.mortes import frase_das_mortes_do_mes
from app.kpis.analitico.recortes import recortes_do_boletim
from app.kpis.analitico.textos import (
    acima_ou_abaixo,
    cabecas,
    contar,
    dinheiro,
    frente_ao_previsto,
    no_plural,
    numero,
    percentual,
)
from app.kpis.analitico.ultimo_dado import frase_das_paradas
from app.schemas.analitico import LinhaDoEstoque, MesDaMortalidade, MorteDoMes, ResumoDoEstoque
from app.schemas.api import Comparacao, EscolhaDoPrevisto, LinhaDoPrevisto, Periodo, PrevistoRealizado
from tests.test_api import carregar_planilha, entrar, usuario_com_senha

METAS = {"fNascimentoPLANEJADO": [["NASCIMENTO", datetime(2025, 7, 10), "Bezerro Mamando", 32, "25/26", 32]],
         "fMortesPLANEJADO": [["MORTE", datetime(2025, 7, 12), "Bezerro Mamando", None, 2, "Meta", "Pasto 1", 40,
                               "25/26"]]}


@pytest.fixture
def fazenda(engine_etl, engine_super, tmp_path):
    return carregar_planilha(engine_etl, engine_super, tmp_path, linhas=METAS)


@pytest.fixture
def consultor(api: TestClient, engine_super, fazenda) -> dict:
    usuario_com_senha(engine_super, "consultor@terra.test", fazendas=[fazenda])
    return entrar(api, "consultor@terra.test")


def boletim(api: TestClient, cabecalho: dict, fazenda, mes: str = "2025-08") -> dict:
    resposta = api.get("/api/v1/dashboards/analitico", headers=cabecalho,
                       params={"fazendas": [str(fazenda)], "mes_referencia": mes, "visao": "safra"})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def test_recortes_do_mes_do_acumulado_e_da_safra(api, consultor, fazenda):
    dados = boletim(api, consultor, fazenda)
    assert (dados["mes_referencia"], dados["inicio_do_periodo"], dados["fim_do_periodo"]) == (
        "2025-08-01", "2025-07-01", "2026-06-01")
    assert [venda["tipo"] for venda in dados["vendas"]] == ["abate", "em_pe"]


def test_o_estoque_do_mes_fecha_e_o_acumulado_soma_a_safra(api, consultor, fazenda):
    estoque = boletim(api, consultor, fazenda)["estoque"]
    total = estoque["mes"][-1]
    assert total["categoria"] == "TOTAL"
    entradas = sum(total[campo] for campo in ("nascimentos", "compras", "desmame_entrada", "transferencia_entrada",
                                              "mudanca_entrada"))
    saidas = sum(total[campo] for campo in ("mortes", "vendas", "desmame_saida", "transferencia_saida",
                                            "consumo_doacao", "mudanca_saida"))
    assert total["estoque_inicial"] + entradas - saidas + total["ajuste"] == total["estoque_final"]
    assert total["vendas"] == 10                                          # as vacas de agosto
    acumulado = estoque["acumulado"]
    assert (acumulado["nascimentos"], acumulado["mortes"], acumulado["vendas"]) == (120, 5, 10)
    assert acumulado["estoque_final"] == total["estoque_final"]
    assert estoque["leitura"][0].startswith("O rebanho fechou agosto/2025 com ")
    assert "vendas 10" in estoque["leitura"][1]


def test_placar_compara_com_a_meta_e_da_o_status_pelo_sentido(api, consultor, fazenda):
    linhas = boletim(api, consultor, fazenda)["placar_zootecnico"]["linhas"]
    nascidos = next(linha for linha in linhas if linha["indicador"] == "Nascimentos")
    assert (nascidos["acumulado"]["previsto"], nascidos["acumulado"]["realizado"]) == (32, 120)
    assert nascidos["acumulado"]["status"] == "verde"                     # nascer mais que o previsto é bom
    mortes = next(linha for linha in linhas if linha["indicador"] == "Mortes")
    assert (mortes["acumulado"]["previsto"], mortes["acumulado"]["realizado"]) == (2, 5)
    assert mortes["acumulado"]["status"] == "vermelho"                    # morrer mais que o previsto é ruim
    assert mortes["meta_periodo"] == 2
    assert mortes["mes"]["realizado"] == 0                                # nenhuma morte em agosto


def test_vendas_listam_os_lotes_do_mes(api, consultor, fazenda):
    em_pe = boletim(api, consultor, fazenda)["vendas"][1]
    assert len(em_pe["lancamentos"]) == 1
    lote = em_pe["lancamentos"][0]
    assert (lote["cabecas"], lote["valor"], lote["kg_vivo"]) == (10, 30000, 4500)
    assert lote["preco_arroba"] == pytest.approx(30000 / (4500 / 30))     # em pé: @ = kg vivo ÷ 30
    assert em_pe["meses"][1]["realizado"] == 10 and em_pe["meses"][2]["realizado"] is None   # depois de agosto: vazio
    assert "10 cabeças em 1 lançamento," in em_pe["leitura"][0]


def test_mortes_do_periodo_com_causa_e_grupo(api, consultor, fazenda):
    mortes = boletim(api, consultor, fazenda, mes="2025-07")["mortes"]
    assert [(morte["causa"], morte["cabecas"]) for morte in mortes["lancamentos"]] == [("COBRA", 5)]
    assert mortes["causas"][0]["causa"] == "COBRA" and mortes["causas"][0]["bezerros"] == 5
    assert mortes["meses"][0]["mortalidade"] == pytest.approx(5 / 1550)
    assert mortes["leitura"][0].startswith("Em julho/2025 morreram 5 cabeças")


def test_nascimentos_compras_e_transferencias(api, consultor, fazenda):
    dados = boletim(api, consultor, fazenda, mes="2025-07")
    nascimentos = dados["nascimentos"]
    assert [(lote["categoria"], lote["cabecas"]) for lote in nascimentos["lancamentos"]] == [("BEZERRO", 120)]
    total = nascimentos["resumo"][0]
    assert (total["indicador"], total["acumulado"]["previsto"], total["acumulado"]["realizado"]) == ("Total", 32, 120)
    assert nascimentos["leitura"][0].startswith("Em julho/2025 nasceram 120 cabeças (")
    assert dados["compras"]["leitura"] == ["Nenhuma compra no período (até julho/2025)."]
    assert dados["transferencias"]["leitura"] == ["Nenhuma transferência no período (até julho/2025)."]
    assert [linha["grupo"] for linha in dados["transferencias"]["saidas"]["resumo"]] == ["SAÍDAS"] * 3


def test_mes_depois_do_ultimo_lancamento_ganha_o_aviso(api, consultor, fazenda):
    dados = boletim(api, consultor, fazenda, mes="2026-03")
    aviso = "Os lançamentos de rebanho vão até agosto/2025; depois disso o saldo só se repete"
    for leitura in (dados["estoque"]["leitura"], dados["lotacao"]["leitura"], dados["mortes"]["leitura"],
                    dados["vendas"][1]["leitura"]):
        assert leitura[0].startswith(aviso)
    # o mês parado não vira "nenhum animal entrou ou saiu": quem lê sabe que falta lançamento
    assert not any(frase.startswith("Nenhum animal") for frase in dados["estoque"]["leitura"])
    assert not boletim(api, consultor, fazenda, mes="2025-08")["estoque"]["leitura"][0].startswith(aviso)


def test_quem_nao_ve_a_fazenda_nao_ve_o_boletim(api, engine_super, fazenda):
    usuario_com_senha(engine_super, "outro@terra.test")
    cabecalho = entrar(api, "outro@terra.test")
    resposta = api.get("/api/v1/dashboards/analitico", headers=cabecalho,
                       params={"fazendas": [str(fazenda)], "mes_referencia": "2025-08"})
    assert resposta.status_code == 403


# --- regras puras -------------------------------------------------------------------------------------------------------


def test_periodo_da_safra_e_do_ano_civil():
    safra = recortes_do_boletim([], date(2026, 3, 1), "safra")
    assert (safra.inicio_do_periodo, safra.fim_do_periodo) == (date(2025, 7, 1), date(2026, 6, 1))
    civil = recortes_do_boletim([], date(2026, 3, 1), "civil")
    assert (civil.inicio_do_periodo, civil.fim_do_periodo) == (date(2026, 1, 1), date(2026, 12, 1))


def test_lotacao_prevista_ignora_mes_do_plano_sem_area():
    # julho tem rebanho planejado e nenhuma área no plano: somado, inflaria a lotação para 3,2 cab/ha
    recortes = recortes_do_boletim([], date(2025, 9, 1), "safra")
    previsto = {date(2025, 7, 1): DoMes(cabecas=1000, area=0), date(2025, 8, 1): DoMes(cabecas=1000, area=500),
                date(2025, 9, 1): DoMes(cabecas=1200, area=500), date(2025, 10, 1): DoMes(cabecas=9000, area=500)}
    assert lotacao_prevista(recortes, previsto) == pytest.approx(2.2)    # outubro fica depois da referência


def test_status_depende_do_sentido_do_indicador():
    assert status(0.05, "maior_melhor", 0.1) == "verde"
    assert status(-0.05, "maior_melhor", 0.1) == "amarelo"
    assert status(-0.2, "maior_melhor", 0.1) == "vermelho"
    assert status(-0.2, "menor_melhor", 0.1) == "verde"
    assert status(0.2, "menor_melhor", 0.1) == "vermelho"
    assert status(0.2, None, 0.1) is None
    sem_previsto = comparado(0, 10, "maior_melhor", 0.1)
    assert (sem_previsto.variacao, sem_previsto.variacao_percentual, sem_previsto.status) == (10, None, None)


def test_sem_meta_no_periodo_nao_ha_previsto():
    # fazenda sem plano: a página manda previsto 0, que no placar pareceria uma meta zerada
    sem_plano = linha_do_placar("VENDAS", "Cabeças", "cab", "maior_melhor", (0, 421), (0, 1682), 0, 0.1)
    assert (sem_plano.mes.previsto, sem_plano.acumulado.previsto, sem_plano.meta_periodo) == (None, None, None)
    assert (sem_plano.acumulado.realizado, sem_plano.acumulado.variacao, sem_plano.acumulado.status) == (1682, None, None)
    com_plano = linha_do_placar("VENDAS", "Cabeças", "cab", "maior_melhor", (0, 421), (500, 450), 800, 0.1)
    assert (com_plano.mes.previsto, com_plano.acumulado.status) == (0, "amarelo")   # mês sem venda prevista


def test_sem_rebanho_a_leitura_diz_que_nao_ha_rebanho():
    recortes = recortes_do_boletim([], date(2026, 6, 1), "safra")
    total = LinhaDoEstoque(categoria="TOTAL", **dict.fromkeys(COLUNAS_DO_ESTOQUE, 0.0))
    zerado = ResumoDoEstoque(**dict.fromkeys(ResumoDoEstoque.model_fields, 0.0))
    assert leitura_do_estoque(recortes, total, zerado, []) == [
        "Não há rebanho nem movimentação de animais no período (até junho/2026)."]


def test_sem_lancamento_financeiro_a_leitura_nao_fala_em_zero():
    recortes = recortes_do_boletim([], date(2025, 9, 1), "safra")
    sem_meta = linha_do_placar("FINANCEIRO", "x", "R$", None, (None, 0), (None, 0), None, 0.1)
    placar = [sem_meta] * 6
    assert leitura_financeira(recortes, placar, [], True) == [
        "Não há lançamentos financeiros no período (até setembro/2025)."]
    receitas = linha_do_placar("FINANCEIRO", "Receitas", "R$", "maior_melhor", (0, 0), (5000, 0), 9000, 0.1)
    assert "o previsto até aqui era de R$ 5.000 em receitas" in leitura_financeira(recortes, [receitas] + placar[1:],
                                                                                   [], True)[0]
    zero = Comparacao(realizado=0, planejado=0, variacao=None, semaforo=None)
    caixa = PrevistoRealizado(periodo=Periodo(inicio=date(2025, 7, 1), fim=date(2025, 9, 1), meses=3),
                              ultimo_mes=date(2025, 9, 1), grupos=[],
                              resultado=LinhaDoPrevisto(nome="RESULTADO", mensal=zero, acumulado=zero),
                              previsto=EscolhaDoPrevisto(tipos=[], tipo=None, versoes=[], versao=None))
    assert frase_do_resultado(recortes, caixa) == (
        "Não há lançamentos financeiros nem fluxo de caixa previsto no período (até setembro/2025).")


def test_so_parte_do_grupo_parou_nomeia_as_fazendas():
    recortes = recortes_do_boletim([], date(2026, 6, 1), "safra")
    assert frase_das_paradas(recortes, [("MIMOSO", date(2025, 8, 1))]) == (
        "Nem todas as fazendas têm lançamentos de rebanho em junho/2026: MIMOSO (até agosto/2025) para antes, e o "
        "saldo dela só se repete.")
    varias = [(f"F{numero_da_fazenda}", date(2025, 8, 1)) for numero_da_fazenda in range(6)]
    assert "F3 (até agosto/2025) e mais 2 param antes" in frase_das_paradas(recortes, varias)


def test_concordancia_com_uma_cabeca():
    assert no_plural(1, "morreu", "morreram") == "morreu" and no_plural(5, "morreu", "morreram") == "morreram"
    morte = MorteDoMes(data=date(2025, 7, 3), causa="COBRA", local=None, categoria="BEZERRO", cabecas=1,
                       peso_vivo_kg=None)
    do_mes = MesDaMortalidade(mes=date(2025, 7, 1), realizado=1, previsto=0, realizado_acumulado=1,
                              previsto_acumulado=0, mortalidade=None, mortalidade_acumulada=None)
    assert frase_das_mortes_do_mes("julho/2025", [morte], do_mes) == "Em julho/2025 morreu 1 cabeça."


def test_numeros_escritos_em_portugues():
    assert numero(1234567.891) == "1.234.568"
    assert numero(1234.5, 2) == "1.234,50"
    assert cabecas(1) == "1 cabeça" and cabecas(1500) == "1.500 cabeças"
    assert percentual(0.047) == "4,7%"
    assert dinheiro(-1234) == "-R$ 1.234"
    assert acima_ou_abaixo(0.12) == "12,0% acima" and acima_ou_abaixo(-0.05) == "5,0% abaixo"
    assert acima_ou_abaixo(0.0001) == "igual"
    assert contar(1, "indicador", "indicadores") == "1 indicador" and contar(0, "lote", "lotes") == "0 lotes"
    assert frente_ao_previsto(0.0001) == "igual ao previsto" and frente_ao_previsto(-0.05, True) == "5,0% abaixo da prevista"
