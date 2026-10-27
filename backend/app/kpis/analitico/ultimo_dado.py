"""Aviso de que o mês de referência passa do último lançamento de rebanho.

Depois do último mês com movimento ou rebanho médio informado, o estoque só repete o saldo (`fato.estoque_mensal` vai
até o mês corrente). Sem o aviso, a folha diria "nenhum animal entrou ou saiu", como se a fazenda tivesse parado no
mês, quando o que falta é o lançamento. O último mês é o mesmo do escopo (`ultimo_mes` de `GET /escopo`).
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.analitico import textos
from app.kpis.analitico.recortes import Recortes

ULTIMO_LANCAMENTO = """
    SELECT f.nome,
           GREATEST((SELECT max(m.competencia) FROM fato.mov_animal m
                     WHERE m.fazenda_id = f.id AND m.cenario = 'realizado'),
                    (SELECT max(r.competencia) FROM fato.rebanho_medio_mensal r
                     WHERE r.fazenda_id = f.id AND r.cenario = 'realizado' AND r.qtd_cab > 0)) AS ultimo_mes,
           -- o saldo no mês é a última linha de cada categoria até ele, como o estoque final das páginas
           (SELECT coalesce(sum(saldo.saldo_final), 0)
            FROM (SELECT DISTINCT ON (e.categoria_bi_id) e.saldo_final
                  FROM fato.estoque_mensal e
                  WHERE e.fazenda_id = f.id AND e.cenario = 'realizado' AND e.competencia <= :mes
                  ORDER BY e.categoria_bi_id, e.competencia DESC) saldo) AS saldo
    FROM core.fazenda f
    WHERE f.id = ANY (CAST(:fazendas AS uuid[]))
    ORDER BY f.nome
"""
MAXIMO_DE_NOMES = 4


@dataclass(frozen=True)
class AvisoDoUltimoDado:
    frase: str | None       # abre a leitura das folhas de rebanho
    todas_paradas: bool     # nenhuma fazenda da seleção tem lançamento no mês de referência


SEM_AVISO = AvisoDoUltimoDado(frase=None, todas_paradas=False)


def aviso_do_ultimo_dado(s: Session, recortes: Recortes) -> AvisoDoUltimoDado:
    parametros = {"fazendas": [str(fazenda) for fazenda in recortes.fazendas], "mes": recortes.mes_referencia}
    com_rebanho = 0
    paradas: list[tuple[str, date]] = []
    for nome, ultimo_mes, saldo in s.execute(text(ULTIMO_LANCAMENTO), parametros):
        # sem rebanho no mês nada se repete (fazenda vendida, encerrada ou só agrícola): não precisa de aviso
        if ultimo_mes is None or not saldo:
            continue
        com_rebanho += 1
        if ultimo_mes < recortes.mes_referencia:
            paradas.append((nome, ultimo_mes))
    if not paradas:
        return SEM_AVISO
    if len(paradas) == com_rebanho:
        ultimo = max(ultimo_mes for _, ultimo_mes in paradas)
        frase = (f"Os lançamentos de rebanho vão até {textos.mes_por_extenso(ultimo)}; depois disso o saldo só se "
                 "repete, sem entradas nem saídas.")
        return AvisoDoUltimoDado(frase=frase, todas_paradas=True)
    return AvisoDoUltimoDado(frase=frase_das_paradas(recortes, paradas), todas_paradas=False)


def frase_das_paradas(recortes: Recortes, paradas: list[tuple[str, date]]) -> str:
    """Só algumas fazendas do grupo param antes: nomeia as primeiras, para quem lê saber onde falta lançamento."""
    nomes = []
    for nome, ultimo_mes in paradas[:MAXIMO_DE_NOMES]:
        nomes.append(f"{nome} (até {textos.mes_por_extenso(ultimo_mes)})")
    lista = ", ".join(nomes)
    if len(paradas) > MAXIMO_DE_NOMES:
        lista += f" e mais {len(paradas) - MAXIMO_DE_NOMES}"
    quantas = len(paradas)
    return (f"Nem todas as fazendas têm lançamentos de rebanho em {textos.mes_por_extenso(recortes.mes_referencia)}: "
            f"{lista} {textos.no_plural(quantas, 'para', 'param')} antes, e o saldo "
            f"{textos.no_plural(quantas, 'dela', 'delas')} só se repete.")
