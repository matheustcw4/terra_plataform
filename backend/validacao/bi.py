"""Números do BI atual, reproduzidos a partir do PRÓPRIO SQL do Power Query (dump dos PBIX) + medidas DAX.

Cada função devolve {(chave_fazenda, competencia): {medida: valor}} com a chave que o BI usa
(planilha: PROP_FAZ; Metryx: idpropfaz = idcustomer||idfarm).
Regras DAX reproduzidas: QTD C do fMovGado; 'Stock Accumulated Final' (acumulado até o fim do mês, só datas que
existem no dCalendar = 2024-07-01..hoje); 'Saldo Acumulado' (Σ amountacc no último dia do mês); somas simples.
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal

from validacao.datalake import competencia, consultar, parse_data, sql_do_pbix

INICIO_CALENDARIO = date(2024, 7, 1)
SAIDAS = {"ABATE", "Consumo/Doação", "MORTE", "EMPÉ", "Transf. Saida"}

Medidas = dict[tuple[str, date], dict[str, Decimal]]


def _d(v) -> Decimal:
    return Decimal(str(v)) if v is not None else Decimal(0)


def _somar(linhas, chave: str, data: str, medidas: dict[str, str], filtro=None) -> Medidas:
    out: Medidas = defaultdict(lambda: defaultdict(Decimal))
    for r in linhas:
        if filtro and not filtro(r):
            continue
        comp = competencia(parse_data(r[data]))
        if comp is None or r[chave] is None:
            continue
        for nome, col in medidas.items():
            out[(r[chave], comp)][nome] += _d(r[col])
    return out


def _meses(ate: date):
    m = INICIO_CALENDARIO
    while m <= ate:
        yield m
        m = date(m.year + m.month // 12, m.month % 12 + 1, 1)


# --- BI Ciclo Completo (planilhas) ------------------------------------------------------------------------------------

def planilha(ate: date) -> Medidas:
    out: Medidas = defaultdict(lambda: defaultdict(Decimal))

    def juntar(parcial: Medidas):
        for k, v in parcial.items():
            out[k].update(v)

    # estoque: Stock Accumulated Final = Σ QTD C com DATA ≤ fim do mês, DATA ∈ dCalendar
    mov = consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "fMovGado"))
    por_mes: dict[str, dict[date, Decimal]] = defaultdict(lambda: defaultdict(Decimal))
    for r in mov:
        dt = parse_data(r["DATA"])
        if dt is None or dt < INICIO_CALENDARIO or dt > date.today():
            continue                                   # sem linha correspondente no dCalendar
        qtd = _d(r["qtd"])
        qtd_c = qtd if qtd < 0 else (-qtd if r["operaÇÃo"] in SAIDAS else qtd)
        por_mes[r["prop_faz"]][competencia(dt)] += qtd_c
    for pf, meses in por_mes.items():
        acumulado = Decimal(0)
        for m in _meses(ate):
            acumulado += meses.get(m, Decimal(0))
            out[(pf, m)]["estoque_final"] = acumulado

    juntar(_somar(consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "pecuarioCompras")), "prop_faz", "DATA",
                  {"compra_cab": "qtd", "compra_valor": "VALOR TOTAL"}))
    juntar(_somar(consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "pecuarioVendaAbate")), "prop_faz", "DATA",
                  {"abate_cab": "qtd", "abate_faturamento": "faturamento", "abate_kg_vivo": "pesovivo_total",
                   "abate_kg_carcaca": "pesomorto_total"}))
    juntar(_somar(consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "pecuarioVendaEmPe")), "prop_faz", "DATA",
                  {"empe_cab": "qtd", "empe_faturamento": "faturamento", "empe_kg_vivo": "pesovivo_total"}))
    juntar(_somar(consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "pecuarioNascimento")), "prop_faz", "DATA",
                  {"nascimento_cab": "qtd"}))
    juntar(_somar(consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "pecuarioMortes")), "prop_faz", "data",
                  {"morte_cab": "qtd"}))
    juntar(_somar(consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "pecuarioRebanhoMedioMensal")), "prop_faz",
                  "DATA", {"rebanho_medio_cab": "qtd_cab", "rebanho_medio_ua": "qtd_ua"}))
    juntar(_somar(consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "fArea")), "prop_faz", "DATA",
                  {"area_total_ha": "Área_total"}))
    dre = consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "financeiroDre"))
    juntar(_somar(dre, "prop_faz", "data_pag", {"fin_credito": "valor"}, lambda r: r["operaÇÃo"] == "C"))
    juntar(_somar(dre, "prop_faz", "data_pag", {"fin_debito": "valor"}, lambda r: r["operaÇÃo"] == "D"))
    return out


# --- BI Versão Metryx -------------------------------------------------------------------------------------------------

def metryx(ate: date) -> Medidas:
    out: Medidas = defaultdict(lambda: defaultdict(Decimal))

    def juntar(parcial: Medidas):
        for k, v in parcial.items():
            out[k].update(v)

    # 'Saldo Acumulado' de um mês = Σ amountacc com date = último dia do mês
    for r in consultar("METRYX", sql_do_pbix("metryx", "fSaldoGado")):
        fim = r["ultimodiames"]
        comp = fim.replace(day=1)
        if INICIO_CALENDARIO <= comp <= ate:
            out[(r["idpropfaz"], comp)]["estoque_final"] += _d(r["amountacc"])

    juntar(_somar(consultar("METRYX", sql_do_pbix("metryx", "pecuarioVendaAbate")), "idpropfaz", "DATA",
                  {"abate_cab": "qtd", "abate_faturamento": "faturamento", "abate_kg_vivo": "pesovivo_total",
                   "abate_kg_carcaca": "pesomorto_total"}))
    juntar(_somar(consultar("METRYX", sql_do_pbix("metryx", "pecuarioVendaEmPe")), "idpropfaz", "DATA",
                  {"empe_cab": "qtd", "empe_faturamento": "faturamento", "empe_kg_vivo": "pesovivo_total"}))
    juntar(_somar(consultar("METRYX", sql_do_pbix("metryx", "pecuarioCompras")), "idpropfaz", "DATA",
                  {"compra_cab": "qtd", "compra_valor": "VALOR TOTAL"}))
    nasc = consultar("METRYX", sql_do_pbix("metryx", "pecuarioNascimento"))
    juntar(_somar(nasc, "idpropfaz", "date", {"nascimento_cab": "amount"}, lambda r: r["idfarm"] is not None))
    mortes = consultar("METRYX", sql_do_pbix("metryx", "pecuarioMortes"))
    juntar(_somar(mortes, "idpropfaz", "DATA", {"morte_cab": "qtd"}))   # 'Dead Quantity' inclui Consumo Abate
    juntar(_somar(consultar("METRYX", sql_do_pbix("metryx", "pecuarioRebanhoMedioMensal")), "idpropfaz", "month",
                  {"rebanho_medio_cab": "amount"}))
    dre = consultar("METRYX", sql_do_pbix("metryx", "financeiroDre"))  # relação pelo VENCIMENTO, fazenda FISCAL
    juntar(_somar(dre, "idpropfaz", "duedate", {"fin_credito": "amountpaid"},
                  lambda r: (r["type"] or "").startswith("Cr") and abs(r["amountpaid"] or 0) < 1e9))
    juntar(_somar(dre, "idpropfaz", "duedate", {"fin_debito": "amountpaid"},
                  lambda r: (r["type"] or "").startswith("D") and abs(r["amountpaid"] or 0) < 1e9))
    return out
