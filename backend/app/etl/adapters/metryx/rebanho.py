"""Rebanho médio realizado do Metryx a partir do `balanco-pecuario`, como o relatório do próprio Metryx.

Rebanho médio do mês = média do saldo de cada dia do mês (cabeças × dias ÷ dias do mês), por fazenda e categoria. O
saldo do dia é o do inventário (saldo.py): em cada série (owner nas categorias comuns, coorte nos bezerros mamando)
vale o último registro do dia, com o mesmo desempate, até a véspera do registro seguinte. No período, a camada de KPI
faz a média dos meses (Σ ÷ nº de meses), e isso dá o número do Metryx: U6, jul–set/2026, 7.257, 7.544 e 8.315 →
7.705 cab, igual ao relatório (27/10/2026).

O endpoint `rebanho-medio-pecuario`, que o BI usa, não é essa média: dá mais cabeças do que o mês teve (U6, jul/2026:
1.496 bezerros com o saldo indo de 107 a 884), e a plataforma mostrava 8.505 no lugar dos 7.705. Defeito do BI que a
plataforma não reproduz (relatório de validação §21); o endpoint continua no bruto, para conferência.

Período: cada série conta do dia do primeiro registro dela até `ate` (o fim do mês do último registro do cliente).
Sem registro novo o saldo continua o mesmo, como no inventário; antes do primeiro registro a série não tem animal.
"""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal

from app.etl.adapters.metryx.saldo import (
    Desempate,
    RegistroBalanco,
    fim_do_mes,
    registro_vence,
    separar_registros,
)
from app.etl.canonical import proximo_mes

MILESIMO = Decimal("0.001")          # a coluna qtd_cab guarda 3 casas

ChaveDoMes = tuple[str, str, date]   # (fazenda, categoria, 1º dia do mês)


def rebanho_medio_mensal(registros: Iterable[RegistroBalanco], ate: date,
                         desempate_mamando: Desempate = "primeiro") -> dict[ChaveDoMes, Decimal]:
    """Rebanho médio de cada mês por fazenda e categoria. Mês sem animal (média zero) fica de fora."""
    separados = separar_registros(registros)
    cabecas_vezes_dias: dict[ChaveDoMes, Decimal] = defaultdict(Decimal)
    for chave_com_owner, registros_da_serie in separados.comuns.items():
        saldos = saldo_de_cada_dia_com_registro(registros_da_serie, "maior")
        somar_a_serie(cabecas_vezes_dias, chave_com_owner, saldos, ate)
    for coorte, registros_da_serie in separados.coortes.items():
        saldos = saldo_de_cada_dia_com_registro(registros_da_serie, desempate_mamando)
        somar_a_serie(cabecas_vezes_dias, coorte, saldos, ate)
    return medias_dos_meses(cabecas_vezes_dias)


def saldo_de_cada_dia_com_registro(registros: list[RegistroBalanco], desempate: Desempate
                                   ) -> list[tuple[date, Decimal]]:
    """Por dia: a quantidade do registro que vale no dia (o desempate é o do inventário), em ordem de data."""
    escolhido: dict[date, RegistroBalanco] = {}
    for registro in registros:
        atual = escolhido.get(registro.data)
        if atual is None or registro_vence(registro, atual, desempate):
            escolhido[registro.data] = registro
    return sorted((dia, registro.quantidade) for dia, registro in escolhido.items())


def somar_a_serie(cabecas_vezes_dias: dict[ChaveDoMes, Decimal], chave: tuple, saldos: list[tuple[date, Decimal]],
                  ate: date) -> None:
    """Cada saldo vale do dia do registro até a véspera do registro seguinte; o último, até `ate`."""
    fazenda, categoria = chave[0], chave[2]
    for posicao, (inicio, quantidade) in enumerate(saldos):
        if posicao + 1 < len(saldos):
            fim = saldos[posicao + 1][0]
        else:
            fim = ate + timedelta(days=1)
        for mes, dias in dias_em_cada_mes(inicio, fim):
            cabecas_vezes_dias[(fazenda, categoria, mes)] += quantidade * dias


def dias_em_cada_mes(inicio: date, fim: date) -> list[tuple[date, int]]:
    """(1º dia do mês, nº de dias) de cada mês entre `inicio` (incluído) e `fim` (excluído)."""
    partes = []
    dia = inicio
    while dia < fim:
        proximo = min(fim, proximo_mes(dia))
        partes.append((dia.replace(day=1), (proximo - dia).days))
        dia = proximo
    return partes


def medias_dos_meses(cabecas_vezes_dias: dict[ChaveDoMes, Decimal]) -> dict[ChaveDoMes, Decimal]:
    medias = {}
    for (fazenda, categoria, mes), total in cabecas_vezes_dias.items():
        if total == 0:
            continue
        dias_do_mes = fim_do_mes(mes).day
        medias[(fazenda, categoria, mes)] = (total / dias_do_mes).quantize(MILESIMO)
    return medias
