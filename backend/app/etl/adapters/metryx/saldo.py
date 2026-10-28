"""Saldo de rebanho do Metryx a partir do `balanco-pecuario`, como o inventário do próprio Metryx.

Saldo de fim de mês por (owner, fazenda, retiro, categoria), devolvido já somado por (fazenda, retiro, categoria),
que o adapter grava como checkpoint em `fato.inventario`. O número tem de bater com o Metryx (pedido do usuário,
20/10/2026); a base é o SQL `fSaldoGado` do BI (docs/referencias/pbix_metryx/power_query.csv), menos onde o BI
diverge do Metryx:
- Só entram registros cuja categoria existe e tem grupo (como o SQL).
- Categorias comuns: saldo = valor do último registro do mês (no último dia com registro, o maior valor) e, nos meses
  seguintes, o último valor conhecido.
- Bezerros/bezerras mamando: por coorte (owner, fazenda, retiro, categoria, nascimento, safra), a mesma coisa: no fim
  do mês vale o último saldo conhecido da coorte. O BI fazia "cada mês vale o MAIOR valor da coorte daquele mês em
  diante": um lote que zera em maio e tem 1 animal de novo em junho aparecia com 1 já em maio, e o inventário do
  Metryx mostra 0 (U6 PARTE V, mai/2026: 32 bezerras no BI, 31 no Metryx). Defeito do BI que a plataforma não
  reproduz (relatório de validação §20).
Empates: nas categorias comuns o SQL fica com o MAIOR valor do último dia (determinístico) e aqui também.
Nos bezerros mamando o SQL pega um registro QUALQUER do último dia (row_number sem desempate): quem decide é a
ordenação do Postgres, que não é estável — nem o BI garante o mesmo número entre duas atualizações. Aqui o desempate
é explícito (`desempate_mamando`). Padrão "primeiro" (o primeiro gravado, na ordem do JSON da API), escolhido em
14/10/2026 para manter a regra do BI: é o que mais coincide com ele (98,0% dos fins de mês idênticos; "maior" 97,4%,
"menor" 97,7%, "último" 97,1%). O resto são só esses empates, que nenhuma regra fixa reproduz.
"""

from bisect import bisect_right
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

GRUPOS_MAMANDO = ("Bezerros Mamando", "Bezerras Mamando")


@dataclass(frozen=True)
class RegistroBalanco:
    fazenda: str              # idFarm
    retiro: str | None        # idRetiro
    categoria: str            # uuidCategory
    owner: str | None
    data: date
    quantidade: Decimal
    grupo: str | None         # categorygroup da categoria (None = categoria sem grupo / desconhecida)
    ano_safra: str | None = None
    nascimento: str | None = None   # birth
    safra: str | None = None        # harvest
    ordem: int = 0                  # posição na origem (índice no JSON da API); decide empates como o BI


Chave = tuple[str, str | None, str]   # (fazenda, retiro, categoria)


def fim_do_mes(d: date) -> date:
    proximo = date(d.year + d.month // 12, d.month % 12 + 1, 1)
    return date.fromordinal(proximo.toordinal() - 1)


def _mes(d: date) -> tuple[int, int]:
    return d.year, d.month


Desempate = Literal["maior", "menor", "primeiro", "ultimo"]


def registro_vence(r: RegistroBalanco, atual: RegistroBalanco, desempate: Desempate) -> bool:
    """`r` substitui `atual` como registro do mês? Data mais recente vence; no mesmo dia, aplica o desempate."""
    if r.data != atual.data:
        return r.data > atual.data
    return {"maior": r.quantidade > atual.quantidade, "menor": r.quantidade < atual.quantidade,
            "primeiro": r.ordem < atual.ordem, "ultimo": r.ordem > atual.ordem}[desempate]


def _ultimo_por_mes(regs: Iterable[RegistroBalanco], desempate: Desempate = "maior"
                    ) -> dict[tuple[int, int], tuple[date, Decimal]]:
    """Por mês: (data do último registro, quantidade escolhida nessa data pelo desempate)."""
    escolhido: dict[tuple[int, int], RegistroBalanco] = {}
    for r in regs:
        m = _mes(r.data)
        if m not in escolhido or registro_vence(r, escolhido[m], desempate):
            escolhido[m] = r
    return {m: (r.data, r.quantidade) for m, r in escolhido.items()}


class _Serie:
    """Série em degrau: valor vigente no fim de cada mês = último ponto com data ≤ fim do mês."""

    def __init__(self, pontos: list[tuple[date, Decimal]]):
        self.pontos = sorted(pontos)
        self.datas = [p[0] for p in self.pontos]

    def em(self, d: date) -> Decimal | None:
        i = bisect_right(self.datas, d)
        return self.pontos[i - 1][1] if i else None


def saldo_fim_de_mes(registros: Iterable[RegistroBalanco],
                     desempate_mamando: Desempate = "primeiro") -> dict[Chave, dict[date, Decimal]]:
    """Saldo no fim de cada mês em que a chave (fazenda, retiro, categoria) tem algum registro.

    Nos meses sem registro o saldo é o do último mês com registro (o motor faz esse forward-fill).
    """
    separados = separar_registros(registros)
    series: dict[Chave, list[_Serie]] = defaultdict(list)
    series_das_categorias_comuns(separados.comuns, series)
    series_dos_bezerros_mamando(separados.coortes, desempate_mamando, series)
    return somar_por_chave(separados.meses_com_registro, series)


@dataclass
class RegistrosSeparados:
    comuns: dict[tuple, list[RegistroBalanco]]        # (fazenda, retiro, categoria, owner) -> registros
    coortes: dict[tuple, list[RegistroBalanco]]       # (fazenda, retiro, categoria, owner, nascimento, safra)
    meses_com_registro: dict[Chave, set[date]]


def separar_registros(registros: Iterable[RegistroBalanco]) -> RegistrosSeparados:
    """Descarta categoria sem grupo (como o SQL) e separa bezerros mamando (por coorte) das demais (por owner)."""
    separados = RegistrosSeparados(defaultdict(list), defaultdict(list), defaultdict(set))
    for registro in registros:
        if registro.grupo is None:
            continue
        chave = (registro.fazenda, registro.retiro, registro.categoria)
        separados.meses_com_registro[chave].add(fim_do_mes(registro.data))
        if eh_bezerro_mamando(registro.grupo):
            coorte = (*chave, registro.owner, registro.nascimento, registro.safra)
            separados.coortes[coorte].append(registro)
        else:
            separados.comuns[(*chave, registro.owner)].append(registro)
    return separados


def eh_bezerro_mamando(grupo: str) -> bool:
    return any(nome in grupo for nome in GRUPOS_MAMANDO)


def series_das_categorias_comuns(comuns: dict[tuple, list[RegistroBalanco]], series: dict) -> None:
    """Categorias comuns: o último valor de cada mês vale até aparecer outro (por owner)."""
    for chave_com_owner, registros in comuns.items():
        pontos = list(_ultimo_por_mes(registros).values())
        series[chave_com_owner[:3]].append(_Serie(pontos))


def series_dos_bezerros_mamando(coortes: dict[tuple, list[RegistroBalanco]], desempate: Desempate,
                                series: dict) -> None:
    """Cada coorte vale, no fim do mês, o último saldo conhecido dela (como o inventário do Metryx)."""
    for coorte, registros in coortes.items():
        pontos = list(_ultimo_por_mes(registros, desempate).values())
        series[coorte[:3]].append(_Serie(pontos))


def somar_por_chave(meses_com_registro: dict[Chave, set[date]], series: dict) -> dict[Chave, dict[date, Decimal]]:
    """Saldo de cada chave no fim de cada mês com registro = soma das séries (owners e coortes) naquela data."""
    resultado: dict[Chave, dict[date, Decimal]] = {}
    for chave, meses in meses_com_registro.items():
        resultado[chave] = {}
        for fim in sorted(meses):
            total = Decimal(0)
            for serie in series[chave]:
                valor = serie.em(fim)
                if valor is not None:
                    total += valor
            resultado[chave][fim] = total
    return resultado
