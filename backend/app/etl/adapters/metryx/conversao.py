"""Conversões dos campos da API Metryx (números, datas, nomes), comuns ao realizado e ao planejamento."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

CARACTERES_INVISIVEIS = dict.fromkeys(map(ord, "​‌‍﻿"))   # aparecem nos nomes de centro de custo


def para_decimal(valor: Any) -> Decimal | None:
    if valor is None or valor == "":
        return None
    return Decimal(str(valor))


def para_data(valor: Any) -> date | None:
    """Datas do Metryx: 'AAAA-MM-DD' (às vezes com hora depois) ou 'DD/MM/AAAA'; nos mensais, 'M-AAAA' / 'MM/AA'
    (o planejamento manda 'M/AA', ex.: '7/25')."""
    if valor is None or valor == "":
        return None
    if isinstance(valor, date):
        return valor
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto[:10], formato).date()
        except ValueError:
            continue
    return _mes_e_ano(texto)


def _mes_e_ano(texto: str) -> date | None:
    for separador in ("-", "/"):
        partes = texto.split(separador)
        if len(partes) != 2 or not all(parte.isdigit() for parte in partes):
            continue
        mes, ano = int(partes[0]), int(partes[1])
        if ano < 100:
            ano += 2000
        if 1 <= mes <= 12:
            return date(ano, mes, 1)
    return None


def sem_vazios(campos: dict[str, Any]) -> dict[str, Any]:
    return {nome: valor for nome, valor in campos.items() if valor is not None}


def limpar_nome(texto: Any) -> str:
    return (texto or "").translate(CARACTERES_INVISIVEIS).strip()
