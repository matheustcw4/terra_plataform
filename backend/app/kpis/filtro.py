"""O recorte que toda página do painel recebe: as fazendas escolhidas e o período (meses fechados).

Os meses podem vir salteados: no MENU o mês é de seleção múltipla, como no BI (jul e set, sem ago). Regra das
medidas do BI, que usam o calendário filtrado: o que é soma (cabeças, R$, rebanho médio) usa só os meses escolhidos;
o que é saldo (estoque final) é o do último mês escolhido (`MAX(dCalendar[Data])`).
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.schemas.api import Periodo


@dataclass(frozen=True)
class Filtro:
    fazendas: list[UUID]
    inicio: date              # 1º dia do primeiro mês
    fim: date                 # 1º dia do último mês (inclusive)
    meses_escolhidos: tuple[date, ...] = ()   # vazio = todos os meses de `inicio` a `fim`

    def parametros(self) -> dict:
        return {"fazendas": [str(fazenda) for fazenda in self.fazendas], "inicio": self.inicio, "fim": self.fim,
                "meses": meses_do_filtro(self)}


def proximo_mes(mes: date) -> date:
    if mes.month == 12:
        return date(mes.year + 1, 1, 1)
    return date(mes.year, mes.month + 1, 1)


def meses_do_filtro(filtro: Filtro) -> list[date]:
    """Os meses que a página soma, em ordem; também o eixo das séries (um ponto por mês, mesmo sem movimento)."""
    if filtro.meses_escolhidos:
        return sorted(filtro.meses_escolhidos)
    meses = []
    mes = filtro.inicio
    while mes <= filtro.fim:
        meses.append(mes)
        mes = proximo_mes(mes)
    return meses


def periodo_do_filtro(filtro: Filtro) -> Periodo:
    """O período que a página respondeu (a tela mostra "jul/25 a jun/26 · 12 meses")."""
    return Periodo(inicio=filtro.inicio, fim=filtro.fim, meses=len(meses_do_filtro(filtro)))
