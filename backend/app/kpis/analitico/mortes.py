"""Mortes do boletim analítico: as mortes do mês de referência (data, causa, local, categoria), a mortalidade mês a
mês prevista × realizada, a mortalidade por grupo contra a meta e as causas por grupo no período até o mês.

Mortalidade = mortes ÷ rebanho médio (a mesma regra da página Mortes); a prevista usa as mortes e o rebanho médio do
cenário planejado.
"""

from collections import defaultdict
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.analitico import textos
from app.kpis.analitico.comparar import dividir
from app.kpis.analitico.recortes import Recortes
from app.kpis.mortes import rebanho_medio_por_grupo
from app.kpis.movimentacao import REBANHO_POR_MES
from app.schemas.analitico import CausaPorGrupo, MesDaMortalidade, MortalidadeDoGrupo, MorteDoMes, SecaoMortes

MORTES_DO_MES = """
    SELECT m.data, coalesce(upper(nullif(btrim(m.causa), '')), 'NÃO INFORMADO') AS causa, m.local,
           coalesce(b.nome, c.nome_origem) AS categoria, m.qtd AS cabecas, m.peso_vivo_total_kg AS peso_vivo_kg
    FROM fato.mov_animal m
    LEFT JOIN dim.categoria_map c ON c.id = m.categoria_map_id
    LEFT JOIN dim.categoria_bi b ON b.id = c.categoria_bi_id
    WHERE m.tipo = 'MORTE' AND m.cenario = 'realizado' AND m.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND m.competencia = :mes
    ORDER BY m.data, categoria
"""
CAUSAS_POR_GRUPO = """
    SELECT coalesce(upper(nullif(btrim(m.causa), '')), 'NÃO INFORMADO') AS causa, b.grupo, sum(m.qtd) AS cabecas
    FROM fato.mov_animal m
    LEFT JOIN dim.categoria_map c ON c.id = m.categoria_map_id
    LEFT JOIN dim.categoria_bi b ON b.id = c.categoria_bi_id
    WHERE m.tipo = 'MORTE' AND m.cenario = 'realizado' AND m.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND m.competencia = ANY (CAST(:meses AS date[]))
    GROUP BY 1, 2
"""
GRUPOS = ["BEZERROS", "JOVENS", "ADULTOS", "GERAL"]


def secao_mortes(s: Session, recortes: Recortes) -> SecaoMortes:
    lancamentos = mortes_do_mes(s, recortes)
    meses = meses_da_mortalidade(s, recortes)
    por_grupo = mortalidade_por_grupo(s, recortes)
    causas = causas_por_grupo(s, recortes)
    return SecaoMortes(lancamentos=lancamentos, meses=meses, por_grupo=por_grupo, causas=causas,
                       leitura=leitura_das_mortes(recortes, lancamentos, meses, por_grupo, causas))


def mortes_do_mes(s: Session, recortes: Recortes) -> list[MorteDoMes]:
    parametros = {"fazendas": [str(fazenda) for fazenda in recortes.fazendas], "mes": recortes.mes_referencia}
    mortes = []
    for linha in s.execute(text(MORTES_DO_MES), parametros).mappings():
        peso = None
        if linha["peso_vivo_kg"] is not None:
            peso = float(linha["peso_vivo_kg"])
        mortes.append(MorteDoMes(data=linha["data"], causa=linha["causa"], local=linha["local"],
                                 categoria=linha["categoria"], cabecas=float(linha["cabecas"] or 0),
                                 peso_vivo_kg=peso))
    return mortes


def rebanho_realizado_por_mes(s: Session, recortes: Recortes) -> dict[date, float]:
    rebanho = {}
    for competencia, cabecas, _ in s.execute(text(REBANHO_POR_MES), recortes.periodo.parametros()):
        rebanho[competencia] = float(cabecas or 0)
    return rebanho


def meses_da_mortalidade(s: Session, recortes: Recortes) -> list[MesDaMortalidade]:
    """Mês a mês no período; o realizado (e a mortalidade) para no mês de referência."""
    rebanho = rebanho_realizado_por_mes(s, recortes)
    meses = []
    soma_do_rebanho = 0.0
    meses_com_rebanho = 0
    for mes in lotes.serie_de_contagem(s, recortes.periodo, "MORTE"):
        if mes.mes > recortes.mes_referencia:
            meses.append(MesDaMortalidade(mes=mes.mes, realizado=None, previsto=mes.planejado,
                                          realizado_acumulado=None, previsto_acumulado=mes.planejado_acumulado,
                                          mortalidade=None, mortalidade_acumulada=None))
            continue
        do_mes = rebanho.get(mes.mes, 0.0)
        soma_do_rebanho += do_mes
        if do_mes:
            meses_com_rebanho += 1
        meses.append(MesDaMortalidade(
            mes=mes.mes, realizado=mes.realizado, previsto=mes.planejado,
            realizado_acumulado=mes.realizado_acumulado, previsto_acumulado=mes.planejado_acumulado,
            mortalidade=dividir(mes.realizado, do_mes),
            mortalidade_acumulada=dividir(mes.realizado_acumulado, dividir(soma_do_rebanho, meses_com_rebanho))))
    return meses


def mortalidade_por_grupo(s: Session, recortes: Recortes) -> list[MortalidadeDoGrupo]:
    acumulado = lotes.somas_por_recorte(s, recortes.acumulado, "MORTE", por="grupo")
    periodo = lotes.somas_por_recorte(s, recortes.periodo, "MORTE", por="grupo")
    rebanho_realizado = rebanho_medio_por_grupo(s, recortes.acumulado)
    rebanho_previsto = rebanho_medio_por_grupo(s, recortes.acumulado, "planejado")
    rebanho_da_meta = rebanho_medio_por_grupo(s, recortes.periodo, "planejado")
    grupos = []
    for grupo in GRUPOS:
        grupos.append(MortalidadeDoGrupo(
            grupo=grupo,
            previsto=dividir(acumulado[("planejado", grupo)].cabecas, rebanho_previsto[grupo]),
            realizado=dividir(acumulado[("realizado", grupo)].cabecas, rebanho_realizado[grupo]),
            meta_periodo=dividir(periodo[("planejado", grupo)].cabecas, rebanho_da_meta[grupo])))
    return grupos


def causas_por_grupo(s: Session, recortes: Recortes) -> list[CausaPorGrupo]:
    por_causa: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    for causa, grupo, cabecas in s.execute(text(CAUSAS_POR_GRUPO), recortes.acumulado.parametros()):
        por_causa[causa][grupo or "SEM GRUPO"] += float(cabecas or 0)
    total_geral = sum(sum(grupos.values()) for grupos in por_causa.values())
    causas = []
    for causa, grupos in por_causa.items():
        total = sum(grupos.values())
        if not total:
            continue
        causas.append(CausaPorGrupo(causa=causa, bezerros=grupos["BEZERROS"], jovens=grupos["JOVENS"],
                                    adultos=grupos["ADULTOS"], sem_grupo=grupos["SEM GRUPO"], total=total,
                                    participacao=dividir(total, total_geral)))
    causas.sort(key=lambda causa: (-causa.total, causa.causa))
    return causas


def leitura_das_mortes(recortes: Recortes, lancamentos: list[MorteDoMes], meses: list[MesDaMortalidade],
                       por_grupo: list[MortalidadeDoGrupo], causas: list[CausaPorGrupo]) -> list[str]:
    mes = textos.mes_por_extenso(recortes.mes_referencia)
    do_mes = mes_de_referencia(meses, recortes.mes_referencia)
    geral = por_grupo[-1]
    if do_mes is None or not do_mes.realizado_acumulado:
        return [frase_sem_mortes(mes, geral)]
    frases = [frase_das_mortes_do_mes(mes, lancamentos, do_mes)]
    if geral.realizado is not None:
        frase = (f"No acumulado até {mes}: {textos.cabecas(do_mes.realizado_acumulado)}, mortalidade de "
                 f"{textos.percentual(geral.realizado, 2)}")
        if geral.previsto is not None:
            frase += f" contra {textos.percentual(geral.previsto, 2)} previstos"
        if geral.meta_periodo is not None:
            frase += f"; a meta do período é {textos.percentual(geral.meta_periodo, 2)}"
        frases.append(frase + ".")
    if causas:
        principal = causas[0]
        frases.append(f"Principal causa no período: {principal.causa.lower()} ({textos.cabecas(principal.total)}, "
                      f"{textos.percentual(principal.participacao or 0)} das mortes).")
    return frases


def frase_sem_mortes(mes: str, geral: MortalidadeDoGrupo) -> str:
    frase = f"Nenhuma morte no período (até {mes})"
    if geral.previsto:
        frase += f"; a mortalidade prevista até aqui era de {textos.percentual(geral.previsto, 2)}"
    return frase + "."


def frase_das_mortes_do_mes(mes: str, lancamentos: list[MorteDoMes], do_mes: MesDaMortalidade) -> str:
    mortas = sum(morte.cabecas for morte in lancamentos)
    if not mortas:
        return f"Nenhuma morte em {mes}."
    frase = f"Em {mes} {textos.no_plural(mortas, 'morreu', 'morreram')} {textos.cabecas(mortas)}"
    if do_mes.mortalidade is not None:
        frase += f" ({textos.percentual(do_mes.mortalidade, 2)} do rebanho médio do mês)"
    return frase + "."


def mes_de_referencia(meses: list[MesDaMortalidade], referencia: date) -> MesDaMortalidade | None:
    for mes in meses:
        if mes.mes == referencia:
            return mes
    return None
