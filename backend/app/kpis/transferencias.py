"""KPIs da página Transferências, a mesma do BI de planilhas: para machos e fêmeas, entrada e saída × realizado e
planejado, com a quantidade, o peso médio e o valor da @; e o gráfico mensal de cabeças que entraram e saíram.

As contas são as de lote (`lotes.py`). A @ da transferência = kg vivo ÷ 30, como na compra; o BI soma a coluna
PESO_ARROBA × QTD da planilha, que pode vir arredondada (A21) ou não bater com o total (A22).
"""

from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.filtro import Filtro, meses_do_filtro, periodo_do_filtro
from app.schemas.api import MesDeTransferencia, Transferencias


def transferencias(s: Session, filtro: Filtro) -> Transferencias:
    return Transferencias(periodo=periodo_do_filtro(filtro), entrada=lotes.quadro(s, filtro, lotes.TRANSF_ENTRADA),
                          saida=lotes.quadro(s, filtro, lotes.TRANSF_SAIDA),
                          serie_mensal=serie_de_transferencias(s, filtro))


def serie_de_transferencias(s: Session, filtro: Filtro) -> list[MesDeTransferencia]:
    entradas = lotes.somas_por_mes(s, filtro, lotes.TRANSF_ENTRADA.tipo_no_fato)
    saidas = lotes.somas_por_mes(s, filtro, lotes.TRANSF_SAIDA.tipo_no_fato)
    serie = []
    for mes in meses_do_filtro(filtro):
        do_mes_entrada = entradas.get((mes, "realizado"), lotes.Somas())
        do_mes_saida = saidas.get((mes, "realizado"), lotes.Somas())
        serie.append(MesDeTransferencia(mes=mes, entradas=do_mes_entrada.cabecas, saidas=do_mes_saida.cabecas))
    return serie
