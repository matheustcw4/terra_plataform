"""Lotes do boletim analítico: os lançamentos do mês de referência, as cabeças previstas × realizadas mês a mês e o
resumo (previsto × realizado, indicador por indicador). Servem às seções de nascimentos, compras, vendas e
transferências, com as regras de arroba e preço das páginas (`app/kpis/lotes.py`).
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.analitico import textos
from app.kpis.analitico.comparar import PrevistoERealizado, Sentido, dividir, linha_do_placar
from app.kpis.analitico.recortes import Recortes
from app.schemas.analitico import LinhaDoPlacar, LoteDoMes, MesComparado
from app.schemas.api import IndicadoresDoLote, QuadroDoLote

LOTES_DO_MES = """
    SELECT m.data, coalesce(b.nome, c.nome_origem) AS categoria, m.contraparte, m.qtd AS cabecas,
           m.peso_vivo_total_kg AS kg_vivo, m.peso_carcaca_total_kg AS kg_carcaca, m.valor_total AS valor
    FROM fato.mov_animal m
    LEFT JOIN dim.categoria_map c ON c.id = m.categoria_map_id
    LEFT JOIN dim.categoria_bi b ON b.id = c.categoria_bi_id
    WHERE m.tipo = :tipo AND m.cenario = 'realizado' AND m.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND m.competencia = :mes
    ORDER BY m.data, categoria
"""

# (indicador, unidade, sentido, valor de um IndicadoresDoLote)
IndicadorDoResumo = tuple[str, str, Sentido, str]


def lotes_do_mes(s: Session, recortes: Recortes, tipo: lotes.TipoDeLote) -> list[LoteDoMes]:
    parametros = {"tipo": tipo.tipo_no_fato, "fazendas": [str(fazenda) for fazenda in recortes.fazendas],
                  "mes": recortes.mes_referencia}
    lancamentos = []
    for linha in s.execute(text(LOTES_DO_MES), parametros).mappings():
        lancamentos.append(lote_do_mes(linha, tipo))
    return lancamentos


def lote_do_mes(linha, tipo: lotes.TipoDeLote) -> LoteDoMes:
    cabecas = float(linha["cabecas"] or 0)
    kg_vivo = numero_ou_vazio(linha["kg_vivo"])
    kg_carcaca = numero_ou_vazio(linha["kg_carcaca"])
    valor = numero_ou_vazio(linha["valor"])
    base_da_arroba = kg_vivo
    if tipo.arroba_pela_carcaca:
        base_da_arroba = kg_carcaca
    arrobas = dividir(base_da_arroba, tipo.kg_por_arroba)
    rendimento = None
    if tipo.arroba_pela_carcaca:
        rendimento = dividir(kg_carcaca, kg_vivo)
    return LoteDoMes(data=linha["data"], categoria=linha["categoria"], contraparte=linha["contraparte"],
                     cabecas=cabecas, kg_vivo=kg_vivo, kg_carcaca=kg_carcaca, arrobas=arrobas,
                     rendimento_carcaca=rendimento, preco_arroba=dividir(valor, arrobas),
                     valor_por_cabeca=dividir(valor, cabecas), preco_kg=dividir(valor, kg_vivo), valor=valor)


def numero_ou_vazio(valor) -> float | None:
    if valor is None:
        return None
    return float(valor)


def meses_comparados(s: Session, recortes: Recortes, tipo: lotes.TipoDeLote) -> list[MesComparado]:
    """Cabeças previstas e realizadas mês a mês no período inteiro; o realizado para no mês de referência."""
    meses = []
    realizado_acumulado = 0.0
    previsto_acumulado = 0.0
    for mes in lotes.serie_mensal(s, recortes.periodo, tipo):
        previsto_acumulado += mes.cabecas_planejadas
        if mes.mes > recortes.mes_referencia:
            meses.append(MesComparado(mes=mes.mes, realizado=None, previsto=mes.cabecas_planejadas,
                                      realizado_acumulado=None, previsto_acumulado=previsto_acumulado))
            continue
        realizado_acumulado += mes.cabecas
        meses.append(MesComparado(mes=mes.mes, realizado=mes.cabecas, previsto=mes.cabecas_planejadas,
                                  realizado_acumulado=realizado_acumulado, previsto_acumulado=previsto_acumulado))
    return meses


def valor_do_indicador(indicadores: IndicadoresDoLote, campo: str) -> float | None:
    if campo == "arrobas_por_cabeca":
        return dividir(indicadores.arrobas, indicadores.cabecas)
    if campo == "valor_por_cabeca":
        return dividir(indicadores.valor, indicadores.cabecas)
    return getattr(indicadores, campo)


def do_quadro(quadro: QuadroDoLote, campo: str) -> PrevistoERealizado:
    return valor_do_indicador(quadro.planejado, campo), valor_do_indicador(quadro.realizado, campo)


def resumo_dos_lotes(grupo: str, quadros: tuple[QuadroDoLote, QuadroDoLote, QuadroDoLote],
                     indicadores: list[IndicadorDoResumo], limiar: float) -> list[LinhaDoPlacar]:
    """Os quadros GERAL do mês, do acumulado e do período inteiro (a meta), nessa ordem."""
    mes, acumulado, periodo = quadros
    linhas = []
    for nome, unidade, sentido, campo in indicadores:
        meta = valor_do_indicador(periodo.planejado, campo)
        linhas.append(linha_do_placar(grupo, nome, unidade, sentido, do_quadro(mes, campo),
                                      do_quadro(acumulado, campo), meta, limiar))
    return linhas


# --- leitura do mês ----------------------------------------------------------------------------------------------


def leitura_dos_lotes(recortes: Recortes, titulo: str, lancamentos: list[LoteDoMes], resumo: list[LinhaDoPlacar],
                      nenhum: str) -> list[str]:
    """`nenhum` começa a frase de quando não houve lançamento, ex.: "Nenhuma venda deste tipo"."""
    mes = textos.mes_por_extenso(recortes.mes_referencia)
    cabecas = resumo[0]
    realizado = cabecas.acumulado.realizado or 0
    if realizado:
        frases = [frase_dos_lotes_do_mes(mes, titulo, lancamentos, nenhum), frase_do_acumulado(mes, resumo)]
    else:
        frases = [f"{nenhum} no período (até {mes})."]
    meta = frase_da_meta(cabecas, realizado)
    if meta is not None:
        frases.append(meta)
    return frases


def frase_dos_lotes_do_mes(mes: str, titulo: str, lancamentos: list[LoteDoMes], nenhum: str) -> str:
    if not lancamentos:
        return f"{nenhum} em {mes}."
    cabecas = sum(lote.cabecas for lote in lancamentos)
    valor = sum(lote.valor or 0 for lote in lancamentos)
    nomes = contrapartes(lancamentos)
    quantos = textos.contar(len(lancamentos), "lançamento", "lançamentos")
    frase = f"{titulo} em {mes}: {textos.cabecas(cabecas)} em {quantos}"
    if nomes:
        frase += f" ({', '.join(nomes[:3])})"
    if valor:
        frase += f", somando {textos.dinheiro(valor)}"
    return frase + "."


def contrapartes(lancamentos: list[LoteDoMes]) -> list[str]:
    return sorted({lote.contraparte for lote in lancamentos if lote.contraparte})


def frase_do_acumulado(mes: str, resumo: list[LinhaDoPlacar]) -> str:
    cabecas = resumo[0]
    frase = f"No acumulado até {mes}: {textos.cabecas(cabecas.acumulado.realizado or 0)}"
    if cabecas.acumulado.variacao_percentual is not None:
        frase += (f", {textos.frente_ao_previsto(cabecas.acumulado.variacao_percentual)} "
                  f"({textos.numero(cabecas.acumulado.previsto)})")
    preco = linha_chamada(resumo, "Preço da @")
    if preco is not None and preco.acumulado.realizado is not None:
        frase += f", ao preço médio de {textos.dinheiro(preco.acumulado.realizado, 2)}/@"
    return frase + "."


def frase_da_meta(cabecas: LinhaDoPlacar, realizado: float) -> str | None:
    if not cabecas.meta_periodo or cabecas.meta_periodo <= realizado:
        return None
    return (f"Para a meta do período ({textos.cabecas(cabecas.meta_periodo)}) faltam "
            f"{textos.cabecas(cabecas.meta_periodo - realizado)}.")


def linha_chamada(linhas: list[LinhaDoPlacar], indicador: str) -> LinhaDoPlacar | None:
    for linha in linhas:
        if linha.indicador == indicador:
            return linha
    return None
