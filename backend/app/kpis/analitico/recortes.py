"""Os três recortes do boletim analítico, todos com as mesmas fazendas: o mês de referência, o acumulado do período
(safra jul–jun ou ano civil) até ele e o período inteiro (a meta). Cada seção chama os KPIs das páginas com esses
recortes; assim o PDF analítico mostra os mesmos números das telas.
"""

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.kpis.filtro import Filtro, meses_do_filtro


@dataclass(frozen=True)
class Recortes:
    fazendas: list[UUID]
    mes_referencia: date
    inicio_do_periodo: date
    fim_do_periodo: date
    visao: str

    @property
    def mes(self) -> Filtro:
        return Filtro(fazendas=self.fazendas, inicio=self.mes_referencia, fim=self.mes_referencia)

    @property
    def acumulado(self) -> Filtro:
        return Filtro(fazendas=self.fazendas, inicio=self.inicio_do_periodo, fim=self.mes_referencia)

    @property
    def periodo(self) -> Filtro:
        return Filtro(fazendas=self.fazendas, inicio=self.inicio_do_periodo, fim=self.fim_do_periodo)

    def meses_do_periodo(self) -> list[date]:
        return meses_do_filtro(self.periodo)

    def meses_ate_a_referencia(self) -> list[date]:
        return meses_do_filtro(self.acumulado)

    def so_do_mes(self, mes: date) -> Filtro:
        return Filtro(fazendas=self.fazendas, inicio=mes, fim=mes)


def recortes_do_boletim(fazendas: list[UUID], mes_referencia: date, visao: str) -> Recortes:
    """Safra: de julho a junho; civil: de janeiro a dezembro. O período é o que contém o mês de referência."""
    if visao == "civil":
        inicio = date(mes_referencia.year, 1, 1)
        fim = date(mes_referencia.year, 12, 1)
    else:
        ano_da_safra = mes_referencia.year
        if mes_referencia.month < 7:
            ano_da_safra -= 1
        inicio = date(ano_da_safra, 7, 1)
        fim = date(ano_da_safra + 1, 6, 1)
    return Recortes(fazendas=fazendas, mes_referencia=mes_referencia, inicio_do_periodo=inicio, fim_do_periodo=fim,
                    visao=visao)
