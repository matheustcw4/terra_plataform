"""Placar de indicadores zootécnicos do boletim analítico: cada indicador com previsto × realizado no mês e no
acumulado, e a meta do período.

Os valores saem dos KPIs das páginas (o quadro GERAL de nascimentos, compras, vendas, transferências e mortes, e o
rebanho médio e a lotação da Movimentação), calculados uma vez por recorte. O previsto do rebanho médio e da lotação
vem do cenário planejado (rebanho médio e área da aba PLANEJADO da planilha).
"""

from collections.abc import Callable
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.analitico import textos
from app.kpis.analitico.comparar import Sentido, dividir, linha_do_placar
from app.kpis.analitico.recortes import Recortes
from app.kpis.compras import compras
from app.kpis.filtro import Filtro
from app.kpis.mortes import mortes
from app.kpis.movimentacao import rebanho_e_area
from app.kpis.nascimentos import nascimentos
from app.kpis.transferencias import transferencias
from app.kpis.vendas import vendas
from app.schemas.analitico import LinhaDoPlacar, SecaoPlacar
from app.schemas.api import ContagemDoRecorte, MortesDoGrupo, NascimentosDoSexo, QuadroDoLote

REBANHO_PREVISTO = """
    SELECT r.competencia, sum(r.qtd_cab) AS cabecas
    FROM fato.rebanho_medio_mensal r
    LEFT JOIN dim.categoria_map m ON m.id = r.categoria_map_id
    WHERE r.cenario = 'planejado' AND r.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND r.competencia = ANY (CAST(:meses AS date[]))
      AND (r.categoria_map_id IS NULL OR m.categoria_bi_id IS NOT NULL)
    GROUP BY r.competencia
"""
AREA_PREVISTA = """
    SELECT a.competencia, sum(a.area_total_ha) AS area
    FROM fato.area_mensal a
    WHERE a.cenario = 'planejado' AND a.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND a.competencia = ANY (CAST(:meses AS date[]))
    GROUP BY a.competencia
"""


@dataclass
class DoRecorte:
    """Os KPIs das páginas num recorte (o quadro GERAL de cada um)."""
    rebanho_medio: float | None
    rebanho_medio_previsto: float | None
    lotacao: float | None
    lotacao_prevista: float | None
    nascimentos: ContagemDoRecorte
    nascimentos_por_sexo: list[NascimentosDoSexo]       # GERAL, MACHO e FÊMEA
    compras: QuadroDoLote
    em_pe: QuadroDoLote
    abate: QuadroDoLote
    transferencia_entrada: QuadroDoLote
    transferencia_saida: QuadroDoLote
    mortes: MortesDoGrupo

    @property
    def mortalidade_prevista(self) -> float | None:
        return dividir(self.mortes.planejado, self.rebanho_medio_previsto)


def do_recorte(s: Session, filtro: Filtro) -> DoRecorte:
    rebanho = rebanho_e_area(s, filtro)
    previsto_cab, previsto_lotacao = rebanho_e_lotacao_previstos(s, filtro)
    transferidos = transferencias(s, filtro)
    nascidos = nascimentos(s, filtro).quadro
    return DoRecorte(
        rebanho_medio=rebanho["rebanho_medio_cab"], rebanho_medio_previsto=previsto_cab,
        lotacao=rebanho["lotacao_cab_ha"], lotacao_prevista=previsto_lotacao,
        nascimentos=nascidos[0], nascimentos_por_sexo=nascidos, compras=compras(s, filtro).quadro[0],
        em_pe=vendas(s, filtro, "em_pe").quadro[0], abate=vendas(s, filtro, "abate").quadro[0],
        transferencia_entrada=transferidos.entrada[0], transferencia_saida=transferidos.saida[0],
        mortes=mortes(s, filtro).quadro[0])


def rebanho_e_lotacao_previstos(s: Session, filtro: Filtro) -> tuple[float | None, float | None]:
    """(rebanho médio previsto, lotação prevista).

    A lotação prevista só usa os meses em que o plano tem área (decidido pelo usuário em 20/10/2026): o BI não tem
    lotação prevista para copiar, e o mês com rebanho planejado e sem área a inflaria (no realizado isso fica como
    no BI, decisão Q13).
    """
    area_por_mes = {}
    for competencia, area in s.execute(text(AREA_PREVISTA), filtro.parametros()):
        area_por_mes[competencia] = float(area or 0)
    total = 0.0
    meses_com_rebanho = 0
    cabecas_com_area = 0.0
    for competencia, cabecas in s.execute(text(REBANHO_PREVISTO), filtro.parametros()):
        total += float(cabecas or 0)
        if cabecas:
            meses_com_rebanho += 1
        if area_por_mes.get(competencia):
            cabecas_com_area += float(cabecas or 0)
    return dividir(total, meses_com_rebanho), dividir(cabecas_com_area, sum(area_por_mes.values()))


@dataclass(frozen=True)
class Indicador:
    grupo: str
    nome: str
    unidade: str
    sentido: Sentido
    valores: Callable[[DoRecorte], tuple[float | None, float | None]]     # (previsto, realizado)


def rebanho_medio(recorte: DoRecorte) -> tuple[float | None, float | None]:
    return recorte.rebanho_medio_previsto, recorte.rebanho_medio


def lotacao(recorte: DoRecorte) -> tuple[float | None, float | None]:
    return recorte.lotacao_prevista, recorte.lotacao


def nascidos(recorte: DoRecorte) -> tuple[float | None, float | None]:
    return recorte.nascimentos.planejado, recorte.nascimentos.realizado


def cabecas_do(quadro: QuadroDoLote) -> tuple[float | None, float | None]:
    return quadro.planejado.cabecas, quadro.realizado.cabecas


def peso_medio_do(quadro: QuadroDoLote) -> tuple[float | None, float | None]:
    return quadro.planejado.peso_medio_kg, quadro.realizado.peso_medio_kg


def preco_arroba_do(quadro: QuadroDoLote) -> tuple[float | None, float | None]:
    return quadro.planejado.preco_arroba, quadro.realizado.preco_arroba


def arrobas_por_cabeca_do(quadro: QuadroDoLote) -> tuple[float | None, float | None]:
    return (dividir(quadro.planejado.arrobas, quadro.planejado.cabecas),
            dividir(quadro.realizado.arrobas, quadro.realizado.cabecas))


INDICADORES = [
    Indicador("REBANHO", "Rebanho médio", "cab", None, rebanho_medio),
    Indicador("REBANHO", "Lotação", "cab/ha", None, lotacao),
    Indicador("NASCIMENTOS", "Nascimentos", "cab", "maior_melhor", nascidos),
    Indicador("COMPRAS", "Cabeças", "cab", None, lambda recorte: cabecas_do(recorte.compras)),
    Indicador("COMPRAS", "Peso médio", "kg", None, lambda recorte: peso_medio_do(recorte.compras)),
    Indicador("COMPRAS", "Preço do kg", "R$/kg", "menor_melhor",
              lambda recorte: (recorte.compras.planejado.preco_kg, recorte.compras.realizado.preco_kg)),
    Indicador("VENDAS EM PÉ", "Cabeças", "cab", "maior_melhor", lambda recorte: cabecas_do(recorte.em_pe)),
    Indicador("VENDAS EM PÉ", "Peso médio", "kg", "maior_melhor", lambda recorte: peso_medio_do(recorte.em_pe)),
    Indicador("VENDAS EM PÉ", "Preço da @", "R$/@", "maior_melhor", lambda recorte: preco_arroba_do(recorte.em_pe)),
    Indicador("VENDAS ABATE", "Cabeças", "cab", "maior_melhor", lambda recorte: cabecas_do(recorte.abate)),
    Indicador("VENDAS ABATE", "Peso médio", "kg", "maior_melhor", lambda recorte: peso_medio_do(recorte.abate)),
    Indicador("VENDAS ABATE", "@ por cabeça", "@", "maior_melhor",
              lambda recorte: arrobas_por_cabeca_do(recorte.abate)),
    Indicador("VENDAS ABATE", "Rendimento de carcaça", "%", "maior_melhor",
              lambda recorte: (recorte.abate.planejado.rendimento_carcaca,
                               recorte.abate.realizado.rendimento_carcaca)),
    Indicador("VENDAS ABATE", "Preço da @", "R$/@", "maior_melhor", lambda recorte: preco_arroba_do(recorte.abate)),
    Indicador("TRANSFERÊNCIAS", "Entradas", "cab", None,
              lambda recorte: cabecas_do(recorte.transferencia_entrada)),
    Indicador("TRANSFERÊNCIAS", "Saídas", "cab", None, lambda recorte: cabecas_do(recorte.transferencia_saida)),
    Indicador("MORTALIDADE", "Mortes", "cab", "menor_melhor",
              lambda recorte: (recorte.mortes.planejado, recorte.mortes.realizado)),
    Indicador("MORTALIDADE", "Mortalidade", "%", "menor_melhor",
              lambda recorte: (recorte.mortalidade_prevista, recorte.mortes.sobre_rebanho_medio)),
]


@dataclass
class TresRecortes:
    mes: DoRecorte
    acumulado: DoRecorte
    periodo: DoRecorte


def tres_recortes(s: Session, recortes: Recortes) -> TresRecortes:
    return TresRecortes(mes=do_recorte(s, recortes.mes), acumulado=do_recorte(s, recortes.acumulado),
                        periodo=do_recorte(s, recortes.periodo))


def linha_do_indicador(indicador: Indicador, valores: TresRecortes, limiar: float) -> LinhaDoPlacar:
    meta, _ = indicador.valores(valores.periodo)
    return linha_do_placar(indicador.grupo, indicador.nome, indicador.unidade, indicador.sentido,
                           indicador.valores(valores.mes), indicador.valores(valores.acumulado), meta, limiar)


def tem_algum_valor(linha: LinhaDoPlacar) -> bool:
    valores = [linha.mes.previsto, linha.mes.realizado, linha.acumulado.previsto, linha.acumulado.realizado,
               linha.meta_periodo]
    return any(valor for valor in valores)


def secao_placar(recortes: Recortes, valores: TresRecortes, limiar: float) -> SecaoPlacar:
    linhas = []
    for indicador in INDICADORES:
        linha = linha_do_indicador(indicador, valores, limiar)
        if tem_algum_valor(linha):
            linhas.append(linha)
    return SecaoPlacar(linhas=linhas, leitura=leitura_do_placar(recortes, linhas))


def leitura_do_placar(recortes: Recortes, linhas: list[LinhaDoPlacar]) -> list[str]:
    mes = textos.mes_por_extenso(recortes.mes_referencia)
    if not linhas:
        return [f"Não há indicadores zootécnicos no período (até {mes})."]
    comparaveis = [linha for linha in linhas if linha.acumulado.variacao_percentual is not None]
    if not comparaveis:
        return [f"O período não tem metas cadastradas: o placar mostra só o realizado até {mes}."]
    por_status = linhas_por_status(comparaveis)
    com_status = len(por_status["verde"]) + len(por_status["amarelo"]) + len(por_status["vermelho"])
    if com_status == 0:
        return [f"No acumulado até {mes}, os indicadores com meta não têm lado certo (rebanho, lotação, compras): "
                "a tabela mostra a diferença para o previsto, sem status."]
    frases = [f"No acumulado até {mes}, {textos.contar(com_status, 'indicador tem', 'indicadores têm')} status: "
              f"{len(por_status['verde'])} no rumo do previsto, {len(por_status['amarelo'])} perto do limite e "
              f"{len(por_status['vermelho'])} fora do previsto."]
    for linha in por_status["vermelho"][:3]:
        frases.append("Atenção: " + frase_do_indicador(linha))
    for linha in por_status["amarelo"][:2]:
        frases.append("Perto do limite: " + frase_do_indicador(linha))
    if por_status["verde"]:
        frases.append("Destaque: " + frase_do_indicador(por_status["verde"][0]))
    return frases


def linhas_por_status(linhas: list[LinhaDoPlacar]) -> dict[str, list[LinhaDoPlacar]]:
    """As linhas de cada cor do status, da maior para a menor diferença ao previsto (as que mais pesam vêm antes)."""
    por_status: dict[str, list[LinhaDoPlacar]] = {"verde": [], "amarelo": [], "vermelho": []}
    for linha in linhas:
        if linha.acumulado.status in por_status:
            por_status[linha.acumulado.status].append(linha)
    for linhas_da_cor in por_status.values():
        linhas_da_cor.sort(key=lambda linha: abs(linha.acumulado.variacao_percentual), reverse=True)
    return por_status


def frase_do_indicador(linha: LinhaDoPlacar) -> str:
    realizado = valor_com_unidade(linha.acumulado.realizado, linha.unidade)
    previsto = valor_com_unidade(linha.acumulado.previsto, linha.unidade)
    nome = linha.indicador if linha.grupo == linha.indicador.upper() else f"{linha.indicador} ({linha.grupo.lower()})"
    diferenca = textos.frente_ao_previsto(linha.acumulado.variacao_percentual)
    if diferenca == "igual ao previsto":
        return f"{nome}: {realizado}, igual ao previsto."
    return f"{nome}: {realizado}, {diferenca} ({previsto})."


def valor_com_unidade(valor: float | None, unidade: str) -> str:
    if valor is None:
        return "—"
    if unidade == "%":
        return textos.percentual(valor, 2)
    if unidade.startswith("R$"):
        return f"{textos.dinheiro(valor, 2)}{unidade[2:]}"
    if unidade == "cab":
        return textos.cabecas(valor)
    return f"{textos.numero(valor, 2)} {unidade}"
