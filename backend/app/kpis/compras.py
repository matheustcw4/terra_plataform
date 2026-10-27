"""KPIs da página Compras, a mesma do BI (docs/analises/01 §5.6 e §7.8): quadros Fêmea / Macho / Geral com cabeças
compradas, peso médio e preço do kg (realizado e planejado), o investimento, o preço da @ de compra, o ágio e a série
mensal. As contas de lote estão em `lotes.py`.

Ágio = (preço da @ de compra − preço da @ vendida) ÷ preço da @ vendida, com a @ vendida de abate e em pé juntos
("AVG Price @ (Em Pe + Abate)": faturamento ÷ (kg de carcaça do abate ÷ 15 + kg vivo em pé ÷ 30)). Positivo = a
reposição custou mais por @ do que a venda rendeu. É do realizado: o BI não tem ágio planejado.
"""

from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.filtro import Filtro, periodo_do_filtro
from app.schemas.api import Compras, QuadroDoLote


def compras(s: Session, filtro: Filtro) -> Compras:
    quadros = lotes.quadro(s, filtro, lotes.COMPRA)
    preco_de_compra = quadro_geral(quadros).realizado.preco_arroba
    preco_de_venda = preco_da_arroba_vendida(s, filtro)
    agio = None
    if preco_de_compra is not None and preco_de_venda:
        agio = (preco_de_compra - preco_de_venda) / preco_de_venda
    return Compras(periodo=periodo_do_filtro(filtro), quadro=quadros, preco_arroba_compra=preco_de_compra,
                   preco_arroba_venda=preco_de_venda, agio=agio,
                   serie_mensal=lotes.serie_mensal(s, filtro, lotes.COMPRA))


def quadro_geral(quadros: list[QuadroDoLote]) -> QuadroDoLote:
    for quadro in quadros:
        if quadro.recorte == "GERAL":
            return quadro
    raise ValueError("quadro GERAL ausente")


def preco_da_arroba_vendida(s: Session, filtro: Filtro, cenario: str = "realizado") -> float | None:
    """Preço médio da @ vendida no período, abate e em pé juntos, como o "AVG Price @ (Em Pe + Abate)" do BI (e o
    "- Forecast", no planejado)."""
    abate = lotes.somas_por_recorte(s, filtro, lotes.ABATE.tipo_no_fato)[(cenario, "GERAL")]
    em_pe = lotes.somas_por_recorte(s, filtro, lotes.VENDA_EM_PE.tipo_no_fato)[(cenario, "GERAL")]
    arrobas = abate.kg_carcaca / lotes.ABATE.kg_por_arroba + em_pe.kg_vivo / lotes.VENDA_EM_PE.kg_por_arroba
    return lotes.dividir(abate.valor + em_pe.valor, arrobas)
