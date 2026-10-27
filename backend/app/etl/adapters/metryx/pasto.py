"""Área de pasto a partir do `utilizacao-pasto` do Metryx (a `fArea` da planilha).

A API devolve as pastagens com cada período de uso: utilização (Pecuária, Agricultura, APP...), status, datas e as
áreas (total, produtiva e calculada). Uma pastagem aparece uma vez por período; o fim de um período costuma ser o
começo do seguinte, e o período atual vem sem fim.

Regra da área do mês (16/10/2026): no último dia do mês, vale para cada pastagem o período mais recente que já
começou e ainda não acabou; entram só as de uso Pecuária. A área total é a da lotação (como pasto + ILP na planilha);
a produtiva vai junto, em coluna própria. Na API real (Serra Dourada) a produtiva vem 0 em várias pastagens grandes,
por isso ela não é a base da lotação.
"""

import unicodedata
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

USO_PECUARIO = "pecuaria"       # `utilizacaoArea` sem acento e em minúsculas


@dataclass(frozen=True)
class PeriodoDePasto:
    pastagem: str               # `id` da pastagem
    inicio: date
    fim: date | None            # vazio: é o uso atual
    pecuario: bool
    area_total: Decimal
    area_produtiva: Decimal


def eh_uso_pecuario(utilizacao: object) -> bool:
    """'Pecuária' com ou sem acento, em qualquer caixa."""
    texto = unicodedata.normalize("NFKD", str(utilizacao or "")).encode("ascii", "ignore").decode()
    return texto.casefold().strip() == USO_PECUARIO


def periodos_vigentes(periodos: list[PeriodoDePasto], dia: date) -> dict[str, PeriodoDePasto]:
    """O período de cada pastagem que vale no dia: o mais recente que já começou e não acabou antes dele. Com isso o
    dia em que um período acaba e o seguinte começa não conta a pastagem duas vezes."""
    vigentes: dict[str, PeriodoDePasto] = {}
    for periodo in periodos:
        if periodo.inicio > dia:
            continue
        if periodo.fim is not None and periodo.fim < dia:
            continue
        atual = vigentes.get(periodo.pastagem)
        if atual is None or periodo.inicio > atual.inicio:
            vigentes[periodo.pastagem] = periodo
    return vigentes


def area_no_dia(periodos: list[PeriodoDePasto], dia: date) -> tuple[Decimal, Decimal]:
    """(área total, área produtiva) das pastagens de uso Pecuária no dia, em hectares."""
    total = Decimal(0)
    produtiva = Decimal(0)
    for periodo in periodos_vigentes(periodos, dia).values():
        if periodo.pecuario:
            total += periodo.area_total
            produtiva += periodo.area_produtiva
    return total, produtiva
