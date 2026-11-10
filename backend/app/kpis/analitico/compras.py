"""Compras do boletim analítico: os lotes comprados no mês de referência, as cabeças previstas × realizadas mês a mês
e o resumo do acumulado, com as regras de arroba e preço da página Compras (@ = kg vivo ÷ 30).

Comprar mais ou menos cabeças não tem lado certo (depende da estratégia da fazenda); pagar menos pelo kg e pela @, sim.
"""

from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.analitico.lotes_do_mes import (
    leitura_dos_lotes,
    linha_chamada,
    lotes_do_mes,
    meses_comparados,
    resumo_dos_lotes,
)
from app.kpis.analitico.placar import TresRecortes
from app.kpis.analitico.recortes import Recortes
from app.kpis.compras import agio, preco_da_arroba_vendida
from app.schemas.analitico import LinhaDoPlacar, SecaoDeCompras

RESUMO = [
    ("Cabeças", "cab", None, "cabecas"),
    ("Peso médio", "kg", None, "peso_medio_kg"),
    ("Preço do kg", "R$/kg", "menor_melhor", "preco_kg"),
    ("Preço da @", "R$/@", "menor_melhor", "preco_arroba"),
    ("Valor por cabeça", "R$/cab", "menor_melhor", "valor_por_cabeca"),
    ("Investimento", "R$", None, "valor"),
]


def secao_compras(s: Session, recortes: Recortes, valores: TresRecortes, limiar: float) -> SecaoDeCompras:
    comprados = lotes_do_mes(s, recortes, lotes.COMPRA)
    quadros = (valores.mes.compras, valores.acumulado.compras, valores.periodo.compras)
    resumo = resumo_dos_lotes("COMPRAS", quadros, RESUMO, limiar)
    preco_de_venda = preco_da_arroba_vendida(s, recortes.acumulado)
    return SecaoDeCompras(tipo="compra", titulo="Compras", lancamentos=comprados,
                          meses=meses_comparados(s, recortes, lotes.COMPRA), resumo=resumo,
                          leitura=leitura_dos_lotes(recortes, "Compras", comprados, resumo, "Nenhuma compra"),
                          preco_arroba_venda=preco_de_venda,
                          agio=agio(preco_da_arroba_comprada(resumo), preco_de_venda))


def preco_da_arroba_comprada(resumo: list[LinhaDoPlacar]) -> float | None:
    linha = linha_chamada(resumo, "Preço da @")
    if linha is None:
        return None
    return linha.acumulado.realizado
