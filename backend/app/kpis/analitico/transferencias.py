"""Transferências do boletim analítico: as entradas e as saídas do mês de referência (de qual fazenda vieram, para
qual foram), as cabeças mês a mês e o resumo do acumulado, com as regras da página Transferências.

Transferir não tem lado certo: as linhas do resumo ficam sem status.
"""

from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.analitico import textos
from app.kpis.analitico.lotes_do_mes import contrapartes, lotes_do_mes, meses_comparados, resumo_dos_lotes
from app.kpis.analitico.placar import DoRecorte, TresRecortes
from app.kpis.analitico.recortes import Recortes
from app.schemas.analitico import LoteDoMes, SecaoDeLotes, SecaoTransferencias
from app.schemas.api import QuadroDoLote

# tipo -> (tipo de lote, título, grupo no resumo)
TIPOS = {"transf_entrada": (lotes.TRANSF_ENTRADA, "Entradas por transferência", "ENTRADAS"),
         "transf_saida": (lotes.TRANSF_SAIDA, "Saídas por transferência", "SAÍDAS")}
RESUMO = [
    ("Cabeças", "cab", None, "cabecas"),
    ("Peso médio", "kg", None, "peso_medio_kg"),
    ("Valor da @", "R$/@", None, "preco_arroba"),
]


def secao_transferencias(s: Session, recortes: Recortes, valores: TresRecortes,
                         limiar: float) -> SecaoTransferencias:
    entradas = secao_do_sentido(s, recortes, valores, "transf_entrada", limiar)
    saidas = secao_do_sentido(s, recortes, valores, "transf_saida", limiar)
    return SecaoTransferencias(entradas=entradas, saidas=saidas,
                               leitura=leitura_das_transferencias(recortes, entradas, saidas))


def secao_do_sentido(s: Session, recortes: Recortes, valores: TresRecortes, tipo: str,
                     limiar: float) -> SecaoDeLotes:
    tipo_de_lote, titulo, grupo = TIPOS[tipo]
    quadros = (quadro_do_sentido(valores.mes, tipo), quadro_do_sentido(valores.acumulado, tipo),
               quadro_do_sentido(valores.periodo, tipo))
    return SecaoDeLotes(tipo=tipo, titulo=titulo, lancamentos=lotes_do_mes(s, recortes, tipo_de_lote),
                        meses=meses_comparados(s, recortes, tipo_de_lote),
                        resumo=resumo_dos_lotes(grupo, quadros, RESUMO, limiar), leitura=[])


def quadro_do_sentido(recorte: DoRecorte, tipo: str) -> QuadroDoLote:
    if tipo == "transf_entrada":
        return recorte.transferencia_entrada
    return recorte.transferencia_saida


def leitura_das_transferencias(recortes: Recortes, entradas: SecaoDeLotes, saidas: SecaoDeLotes) -> list[str]:
    mes = textos.mes_por_extenso(recortes.mes_referencia)
    entrou = entradas.resumo[0].acumulado.realizado or 0
    saiu = saidas.resumo[0].acumulado.realizado or 0
    if not entrou and not saiu:
        return [f"Nenhuma transferência no período (até {mes})."]
    return [frase_do_mes(mes, entradas.lancamentos, saidas.lancamentos),
            f"No acumulado até {mes}: {movimento(entrou, saiu)}."]


def frase_do_mes(mes: str, entradas: list[LoteDoMes], saidas: list[LoteDoMes]) -> str:
    entrou = sum(lote.cabecas for lote in entradas)
    saiu = sum(lote.cabecas for lote in saidas)
    if not entrou and not saiu:
        return f"Nenhuma transferência em {mes}."
    return f"Em {mes} {movimento(entrou, saiu, de_onde(entradas), para_onde(saidas))}."


def movimento(entrou: float, saiu: float, origem: str = "", destino: str = "") -> str:
    """Ex.: "entraram 30 cabeças (de X) e saiu 1 cabeça (para Y)", só com o lado que houve."""
    partes = []
    if entrou:
        partes.append(f"{textos.no_plural(entrou, 'entrou', 'entraram')} {textos.cabecas(entrou)}{origem}")
    if saiu:
        partes.append(f"{textos.no_plural(saiu, 'saiu', 'saíram')} {textos.cabecas(saiu)}{destino}")
    return " e ".join(partes)


def de_onde(lancamentos: list[LoteDoMes]) -> str:
    nomes = contrapartes(lancamentos)
    if not nomes:
        return ""
    return f" (de {', '.join(nomes[:3])})"


def para_onde(lancamentos: list[LoteDoMes]) -> str:
    nomes = contrapartes(lancamentos)
    if not nomes:
        return ""
    return f" (para {', '.join(nomes[:3])})"
