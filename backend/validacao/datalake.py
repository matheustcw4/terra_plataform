"""Acesso SOMENTE LEITURA aos datalakes atuais do BI (Pentaho -> Postgres) e ao SQL dos PBIX.

Uso exclusivo da validação de paridade: as tabelas `stg_*` são o que os PBIX leem hoje.
Nunca selecionar `stg_customers.token` (tokens Metryx em texto puro).
"""

import csv
import os
import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from app.core.config import RAIZ_REPO

REFERENCIAS = RAIZ_REPO / "docs" / "referencias"


def conninfo(banco: str) -> str:
    return os.environ.get(f"DATALAKE_{banco}_URL", f"host=127.0.0.1 port=5432 dbname={banco} user=postgres")


@contextmanager
def conectar(banco: str) -> Iterator[psycopg.Connection]:
    with psycopg.connect(conninfo(banco), options="-c default_transaction_read_only=on", row_factory=dict_row) as c:
        yield c


def consultar(banco: str, sql: str, params: tuple | dict | None = None) -> list[dict]:
    if re.search(r"\btoken\b", sql, re.IGNORECASE):
        raise ValueError("consulta tocaria a coluna de token Metryx — proibido")
    with conectar(banco) as c:
        return c.execute(sql, params).fetchall()


def sql_do_pbix(pbix: str, tabela: str) -> str:
    """Extrai o SQL nativo (Odbc.Query) da tabela `tabela` do dump do PBIX ('ciclo' ou 'metryx')."""
    csv.field_size_limit(10**9)
    with open(REFERENCIAS / f"pbix_{pbix}" / "power_query.csv", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["TableName"] == tabela:
                # a consulta termina em `"),` (seguem outras etapas do M) ou em `")` + `in` (é a última etapa)
                m = re.search(r'Odbc\.Query\("dsn=[^"]+",\s*"(.*?)"\)\s*(?:,|in\s)', row["Expression"], re.DOTALL)
                if not m:
                    raise ValueError(f"{tabela}: Odbc.Query não encontrado")
                return (m.group(1).replace('""', '"').replace("#(lf)", "\n").replace("#(tab)", " ")
                        .replace("#(cr)", ""))
    raise KeyError(tabela)


_FORMATOS = ("%Y/%m/%d", "%Y-%m-%d", "%d/%m/%Y", "%d/%m/%y")


def parse_data(valor) -> date | None:
    """Datas como chegam nas stg_* (texto em vários formatos, timestamp). 'MM/AAAA' -> dia 1."""
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    s = str(valor).strip()[:10]
    if not s:
        return None
    if re.fullmatch(r"\d{1,2}/\d{4}", s):
        mes, ano = s.split("/")
        return date(int(ano), int(mes), 1)
    if re.fullmatch(r"\d{1,2}-\d{4}", s):          # 'M-AAAA' (rebanho médio Metryx)
        mes, ano = s.split("-")
        return date(int(ano), int(mes), 1)
    for f in _FORMATOS:
        try:
            return datetime.strptime(s, f).date()
        except ValueError:
            continue
    return None


def jsonavel(x):
    """Converte o que vem do Postgres para tipos JSON (raw.payload)."""
    from decimal import Decimal
    if isinstance(x, dict):
        return {k: jsonavel(v) for k, v in x.items()}
    if isinstance(x, list):
        return [jsonavel(v) for v in x]
    if isinstance(x, date):
        return x.isoformat()
    if isinstance(x, Decimal):
        return float(x)
    return x


def competencia(d: date | None) -> date | None:
    return d.replace(day=1) if d else None


__all__ = ["Path", "competencia", "conectar", "consultar", "jsonavel", "parse_data", "sql_do_pbix"]
