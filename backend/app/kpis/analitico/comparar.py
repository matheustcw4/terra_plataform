"""Previsto × realizado de um indicador, com a variação e o status (o semáforo das páginas e do BI).

O status depende do sentido do indicador: em nascimentos, vendas e preço de venda, passar do previsto é bom; em
mortes e custos, é ruim; em rebanho, lotação, compras e transferências não há lado certo, e o status fica vazio. O
limiar entre verde e amarelo vem de `dim.parametro` (o mesmo do Previsto × Realizado).
"""

from typing import Literal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.analitico import Comparado, LinhaDoPlacar

Sentido = Literal["maior_melhor", "menor_melhor"] | None
PrevistoERealizado = tuple[float | None, float | None]

LIMIAR = "SELECT valor FROM dim.parametro WHERE chave = 'semaforo_limiar'"


def limiar_do_semaforo(s: Session) -> float:
    return float(s.scalar(text(LIMIAR)))


def comparado(previsto: float | None, realizado: float | None, sentido: Sentido, limiar: float) -> Comparado:
    variacao = None
    variacao_percentual = None
    if previsto is not None and realizado is not None:
        variacao = realizado - previsto
        if previsto != 0:
            variacao_percentual = variacao / abs(previsto)
    return Comparado(previsto=previsto, realizado=realizado, variacao=variacao,
                     variacao_percentual=variacao_percentual, status=status(variacao_percentual, sentido, limiar))


def linha_do_placar(grupo: str, indicador: str, unidade: str, sentido: Sentido, mes: PrevistoERealizado,
                    acumulado: PrevistoERealizado, meta: float | None, limiar: float) -> LinhaDoPlacar:
    """Uma linha do placar: o mês e o acumulado contra o previsto, e a meta do período.

    Sem meta no período (zero ou vazio) não há previsto: a fazenda sem plano mostraria um previsto 0, com variação e
    status de uma meta que não existe.
    """
    previsto_mes, realizado_mes = mes
    previsto_acumulado, realizado_acumulado = acumulado
    if not meta:
        previsto_mes = None
        previsto_acumulado = None
        meta = None
    return LinhaDoPlacar(grupo=grupo, indicador=indicador, unidade=unidade,
                         mes=comparado(previsto_mes, realizado_mes, sentido, limiar),
                         acumulado=comparado(previsto_acumulado, realizado_acumulado, sentido, limiar),
                         meta_periodo=meta)


def status(variacao_percentual: float | None, sentido: Sentido, limiar: float) -> str | None:
    """Verde: no sentido bom; amarelo: até o limiar no sentido ruim; vermelho: além dele."""
    if variacao_percentual is None or sentido is None:
        return None
    no_sentido_ruim = -variacao_percentual
    if sentido == "menor_melhor":
        no_sentido_ruim = variacao_percentual
    if no_sentido_ruim <= 0:
        return "verde"
    if no_sentido_ruim <= limiar:
        return "amarelo"
    return "vermelho"


def dividir(numerador: float | None, denominador: float | None) -> float | None:
    """Sem base (zero ou vazio) não há razão: a folha mostra traço, e não um 0 que parece resultado."""
    if numerador is None or not denominador:
        return None
    return numerador / denominador
