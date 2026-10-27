"""KPIs das páginas Venda Abate e Venda em Pé, as mesmas do BI (docs/analises/01 §7.6–7.7). As contas são as de
`lotes.py`; aqui só se escolhe o tipo de venda."""

from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.filtro import Filtro, periodo_do_filtro
from app.schemas.api import Vendas

TIPOS = {"abate": lotes.ABATE, "em_pe": lotes.VENDA_EM_PE}


def vendas(s: Session, filtro: Filtro, tipo: str) -> Vendas:
    tipo_de_lote = TIPOS[tipo]
    return Vendas(periodo=periodo_do_filtro(filtro), tipo=tipo, quadro=lotes.quadro(s, filtro, tipo_de_lote),
                  serie_mensal=lotes.serie_mensal(s, filtro, tipo_de_lote))
