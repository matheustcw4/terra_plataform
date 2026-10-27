"""Vendas (abate e em pé) do boletim analítico: os lotes vendidos no mês de referência, as cabeças previstas ×
realizadas mês a mês no período e o resumo do acumulado (as mesmas regras de arroba e preço da página Vendas).
"""

from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.analitico.lotes_do_mes import (
    IndicadorDoResumo,
    leitura_dos_lotes,
    lotes_do_mes,
    meses_comparados,
    resumo_dos_lotes,
)
from app.kpis.analitico.placar import DoRecorte, TresRecortes
from app.kpis.analitico.recortes import Recortes
from app.schemas.analitico import SecaoDeLotes
from app.schemas.api import QuadroDoLote

TIPOS = {"abate": (lotes.ABATE, "Vendas abate"), "em_pe": (lotes.VENDA_EM_PE, "Vendas em pé")}

# (indicador, unidade, sentido, só no abate, valor de um IndicadoresDoLote)
RESUMO = [
    ("Cabeças", "cab", "maior_melhor", False, "cabecas"),
    ("Peso médio", "kg", "maior_melhor", False, "peso_medio_kg"),
    ("Rendimento de carcaça", "%", "maior_melhor", True, "rendimento_carcaca"),
    ("@ por cabeça", "@", "maior_melhor", False, "arrobas_por_cabeca"),
    ("Preço do kg", "R$/kg", "maior_melhor", False, "preco_kg"),
    ("Preço da @", "R$/@", "maior_melhor", False, "preco_arroba"),
    ("Valor por cabeça", "R$/cab", "maior_melhor", False, "valor_por_cabeca"),
    ("Faturamento", "R$", "maior_melhor", False, "valor"),
]


def secoes_de_vendas(s: Session, recortes: Recortes, valores: TresRecortes, limiar: float) -> list[SecaoDeLotes]:
    secoes = []
    for tipo in TIPOS:
        secoes.append(secao_venda(s, recortes, valores, tipo, limiar))
    return secoes


def secao_venda(s: Session, recortes: Recortes, valores: TresRecortes, tipo: str, limiar: float) -> SecaoDeLotes:
    tipo_de_lote, titulo = TIPOS[tipo]
    vendidos = lotes_do_mes(s, recortes, tipo_de_lote)
    quadros = (quadro_do_tipo(valores.mes, tipo), quadro_do_tipo(valores.acumulado, tipo),
               quadro_do_tipo(valores.periodo, tipo))
    resumo = resumo_dos_lotes("VENDAS", quadros, indicadores_da_venda(tipo), limiar)
    return SecaoDeLotes(tipo=tipo, titulo=titulo, lancamentos=vendidos,
                        meses=meses_comparados(s, recortes, tipo_de_lote), resumo=resumo,
                        leitura=leitura_dos_lotes(recortes, titulo, vendidos, resumo, "Nenhuma venda deste tipo"))


def quadro_do_tipo(recorte: DoRecorte, tipo: str) -> QuadroDoLote:
    if tipo == "abate":
        return recorte.abate
    return recorte.em_pe


def indicadores_da_venda(tipo: str) -> list[IndicadorDoResumo]:
    """O rendimento de carcaça só existe no abate."""
    indicadores = []
    for nome, unidade, sentido, so_no_abate, campo in RESUMO:
        if so_no_abate and tipo != "abate":
            continue
        indicadores.append((nome, unidade, sentido, campo))
    return indicadores
