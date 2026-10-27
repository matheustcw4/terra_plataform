"""Movimentação do estoque e lotação do boletim analítico.

- Movimentação do mês: cada categoria BI com o estoque inicial, cada entrada e cada saída e o estoque final, de
  `fato.estoque_mensal` (o mesmo estoque da página Movimentação, com o ajuste de inventário à vista).
- Acumulado: o período até o mês de referência somado; o estoque inicial é o do começo do período (ou do primeiro mês
  da fazenda, se ela começou depois).
- Lotação: mês a mês, rebanho médio ÷ área do mesmo mês; no período, a regra do BI e das páginas (Σ cabeças ÷ Σ área
  dos meses, Q13). O previsto usa o rebanho médio e a área do cenário planejado.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.analitico import textos
from app.kpis.analitico.comparar import dividir
from app.kpis.analitico.recortes import Recortes
from app.kpis.movimentacao import estoque_final, rebanho_e_area
from app.schemas.analitico import (
    FatiaDoRebanho,
    LinhaDoEstoque,
    MesDaLotacao,
    ResumoDoEstoque,
    SecaoEstoque,
    SecaoLotacao,
)

COLUNAS_DO_ESTOQUE = {
    "estoque_inicial": "saldo_inicial", "nascimentos": "nascimento", "compras": "compra",
    "desmame_entrada": "desmame_entrada", "transferencia_entrada": "transf_entrada",
    "mudanca_entrada": "mudanca_entrada", "mortes": "morte", "vendas": "abate + e.venda_em_pe",
    "desmame_saida": "desmame_saida", "transferencia_saida": "transf_saida", "consumo_doacao": "consumo_doacao",
    "mudanca_saida": "mudanca_saida", "ajuste": "ajuste", "estoque_final": "saldo_final",
}
SOMAS_DO_ESTOQUE = ", ".join(f"sum(e.{coluna}) AS {campo}" for campo, coluna in COLUNAS_DO_ESTOQUE.items())
ESTOQUE_DO_MES = f"""
    SELECT b.nome AS categoria, {SOMAS_DO_ESTOQUE}
    FROM fato.estoque_mensal e JOIN dim.categoria_bi b ON b.id = e.categoria_bi_id
    WHERE e.cenario = 'realizado' AND e.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND e.competencia = :mes
    GROUP BY b.id, b.nome
    ORDER BY b.id
"""
FLUXOS_DO_PERIODO = f"""
    SELECT {SOMAS_DO_ESTOQUE}
    FROM fato.estoque_mensal e
    WHERE e.cenario = 'realizado' AND e.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND e.competencia BETWEEN :inicio AND :fim
"""
# o estoque inicial de cada fazenda é o do primeiro mês dela dentro do período
ESTOQUE_NO_INICIO = """
    SELECT coalesce(sum(e.saldo_inicial), 0)
    FROM fato.estoque_mensal e
    JOIN (SELECT fazenda_id, min(competencia) AS primeiro
          FROM fato.estoque_mensal
          WHERE cenario = 'realizado' AND fazenda_id = ANY (CAST(:fazendas AS uuid[]))
            AND competencia BETWEEN :inicio AND :fim
          GROUP BY fazenda_id) p ON p.fazenda_id = e.fazenda_id AND p.primeiro = e.competencia
    WHERE e.cenario = 'realizado'
"""
REBANHO_POR_MES = """
    SELECT r.competencia, r.cenario, sum(r.qtd_cab) AS cabecas, sum(r.qtd_ua_informada) AS ua
    FROM fato.rebanho_medio_mensal r
    LEFT JOIN dim.categoria_map m ON m.id = r.categoria_map_id
    WHERE r.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND r.competencia BETWEEN :inicio AND :fim
      AND (r.categoria_map_id IS NULL OR m.categoria_bi_id IS NOT NULL)    -- categoria pendente fica fora
    GROUP BY r.competencia, r.cenario
"""
AREA_POR_MES = """
    SELECT a.competencia, a.cenario, sum(a.area_total_ha) AS area
    FROM fato.area_mensal a
    WHERE a.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND a.competencia BETWEEN :inicio AND :fim
    GROUP BY a.competencia, a.cenario
"""


# --- movimentação do estoque -----------------------------------------------------------------------------------------


def secao_estoque(s: Session, recortes: Recortes, sem_lancamento_no_mes: bool = False) -> SecaoEstoque:
    """`sem_lancamento_no_mes`: o mês passa do último lançamento de todas as fazendas (o aviso do boletim já diz)."""
    linhas = estoque_do_mes(s, recortes)
    acumulado = resumo_do_periodo(s, recortes)
    distribuicao = distribuicao_final(linhas)
    leitura = leitura_do_estoque(recortes, linhas[-1], acumulado, distribuicao, sem_lancamento_no_mes)
    return SecaoEstoque(mes=linhas, acumulado=acumulado, distribuicao_final=distribuicao, leitura=leitura)


def estoque_do_mes(s: Session, recortes: Recortes) -> list[LinhaDoEstoque]:
    """As categorias com algum animal ou movimento no mês e, por último, o TOTAL."""
    parametros = {"fazendas": [str(fazenda) for fazenda in recortes.fazendas], "mes": recortes.mes_referencia}
    linhas = []
    total = defaultdict(float)
    for registro in s.execute(text(ESTOQUE_DO_MES), parametros).mappings():
        valores = {campo: float(registro[campo] or 0) for campo in COLUNAS_DO_ESTOQUE}
        if not any(valores.values()):
            continue
        linhas.append(LinhaDoEstoque(categoria=registro["categoria"], **valores))
        for campo, valor in valores.items():
            total[campo] += valor
    linhas.append(LinhaDoEstoque(categoria="TOTAL", **{campo: total[campo] for campo in COLUNAS_DO_ESTOQUE}))
    return linhas


def resumo_do_periodo(s: Session, recortes: Recortes) -> ResumoDoEstoque:
    parametros = recortes.acumulado.parametros()
    fluxos = s.execute(text(FLUXOS_DO_PERIODO), parametros).mappings().one()
    entrada_e_saida = {campo: float(fluxos[campo] or 0) for campo in COLUNAS_DO_ESTOQUE}
    return ResumoDoEstoque(
        estoque_inicial=float(s.scalar(text(ESTOQUE_NO_INICIO), parametros) or 0),
        nascimentos=entrada_e_saida["nascimentos"], compras=entrada_e_saida["compras"],
        vendas=entrada_e_saida["vendas"], mortes=entrada_e_saida["mortes"],
        consumo_doacao=entrada_e_saida["consumo_doacao"],
        transferencia_entrada=entrada_e_saida["transferencia_entrada"],
        transferencia_saida=entrada_e_saida["transferencia_saida"], ajuste=entrada_e_saida["ajuste"],
        estoque_final=estoque_final(s, recortes.mes))


def distribuicao_final(linhas: list[LinhaDoEstoque]) -> list[FatiaDoRebanho]:
    total = linhas[-1].estoque_final
    fatias = []
    for linha in linhas[:-1]:
        if linha.estoque_final:
            fatias.append(FatiaDoRebanho(categoria=linha.categoria, cabecas=linha.estoque_final,
                                         participacao=dividir(linha.estoque_final, total)))
    fatias.sort(key=lambda fatia: fatia.cabecas, reverse=True)
    return fatias


def leitura_do_estoque(recortes: Recortes, total: LinhaDoEstoque, acumulado: ResumoDoEstoque,
                       distribuicao: list[FatiaDoRebanho], sem_lancamento_no_mes: bool = False) -> list[str]:
    mes = textos.mes_por_extenso(recortes.mes_referencia)
    if sem_rebanho(acumulado):
        return [f"Não há rebanho nem movimentação de animais no período (até {mes})."]
    frases = [frase_do_rebanho(mes, acumulado)]
    if not sem_lancamento_no_mes:
        frases.append(frase_das_entradas_e_saidas(total))
    if total.desmame_entrada or total.mudanca_entrada:
        frases.append(frase_das_trocas_de_categoria(total))
    if distribuicao and distribuicao[0].participacao is not None:
        maior = distribuicao[0]
        frases.append(f"A maior categoria é {maior.categoria}, com {textos.cabecas(maior.cabecas)} "
                      f"({textos.percentual(maior.participacao)} do rebanho).")
    if total.ajuste:
        frases.append(f"Houve ajuste de inventário de {textos.numero(total.ajuste)} cabeças no mês: é a diferença "
                      "entre o saldo informado pela fonte e os movimentos lançados.")
    return frases


def sem_rebanho(acumulado: ResumoDoEstoque) -> bool:
    """Nem estoque nem movimento no período: fazenda só agrícola, administrativa ou ainda sem lançamento de gado."""
    movimentado = 0.0
    for valor in acumulado.model_dump().values():
        movimentado += abs(valor)
    return movimentado == 0


def frase_das_trocas_de_categoria(total: LinhaDoEstoque) -> str:
    """Desmame e mudança de categoria só trocam o animal de linha; a frase cita só o que aconteceu no mês."""
    if not total.desmame_entrada:
        verbo = textos.no_plural(total.mudanca_entrada, "Mudou", "Mudaram")
        return f"{verbo} de categoria {textos.cabecas(total.mudanca_entrada)} (não altera o total)."
    if not total.mudanca_entrada:
        verbo = textos.no_plural(total.desmame_entrada, "Mudou", "Mudaram")
        return f"{verbo} de categoria {textos.cabecas(total.desmame_entrada)} pelo desmame (não altera o total)."
    return (f"Mudaram de categoria {textos.cabecas(total.desmame_entrada)} pelo desmame e "
            f"{textos.cabecas(total.mudanca_entrada)} por mudança de categoria (não alteram o total).")


def frase_do_rebanho(mes: str, acumulado: ResumoDoEstoque) -> str:
    variacao = dividir(acumulado.estoque_final - acumulado.estoque_inicial, acumulado.estoque_inicial)
    frase = f"O rebanho fechou {mes} com {textos.cabecas(acumulado.estoque_final)}"
    if variacao is None:
        return frase + "."
    if textos.acima_ou_abaixo(variacao) == "igual":
        return frase + f", o mesmo número do começo do período ({textos.numero(acumulado.estoque_inicial)})."
    return frase + (f", {textos.acima_ou_abaixo(variacao)} do começo do período "
                    f"({textos.numero(acumulado.estoque_inicial)}).")


def frase_das_entradas_e_saidas(total: LinhaDoEstoque) -> str:
    entradas = {"nascimentos": total.nascimentos, "compras": total.compras,
                "transferências": total.transferencia_entrada}
    saidas = {"vendas": total.vendas, "mortes": total.mortes, "consumo/doação": total.consumo_doacao,
              "transferências": total.transferencia_saida}
    entrou = sum(entradas.values())
    saiu = sum(saidas.values())
    if not entrou and not saiu:
        return "Nenhum animal entrou na fazenda ou saiu dela no mês."
    parte_da_entrada = "não entrou nenhum animal"
    if entrou:
        verbo = textos.no_plural(entrou, "entrou", "entraram")
        parte_da_entrada = f"{verbo} {textos.cabecas(entrou)}{detalhe(entradas)}"
    parte_da_saida = "não saiu nenhum"
    if saiu:
        verbo = textos.no_plural(saiu, "saiu", "saíram")
        parte_da_saida = f"{verbo} {textos.cabecas(saiu)}{detalhe(saidas)}"
    return f"No mês {parte_da_entrada} e {parte_da_saida}."


def detalhe(partes: dict[str, float]) -> str:
    """{"vendas": 39, "mortes": 2, "compras": 0} -> " (vendas 39, mortes 2)"; nada -> ""."""
    itens = []
    for nome, valor in partes.items():
        if valor:
            itens.append(f"{nome} {textos.numero(valor)}")
    if not itens:
        return ""
    return " (" + ", ".join(itens) + ")"


# --- lotação ----------------------------------------------------------------------------------------------------------


@dataclass
class DoMes:
    cabecas: float = 0.0
    ua: float | None = None
    area: float = 0.0


def secao_lotacao(s: Session, recortes: Recortes, estoque: SecaoEstoque) -> SecaoLotacao:
    realizado, previsto = rebanho_e_area_por_mes(s, recortes)
    meses = meses_da_lotacao(recortes, realizado, previsto)
    no_periodo = rebanho_e_area(s, recortes.acumulado)
    prevista = lotacao_prevista(recortes, previsto)
    lotacoes = [mes.lotacao_cab_ha for mes in meses if mes.lotacao_cab_ha is not None]
    inicial = estoque.acumulado.estoque_inicial
    final = estoque.acumulado.estoque_final
    secao = SecaoLotacao(
        estoque_inicial=inicial, estoque_final=final, variacao_do_rebanho=dividir(final - inicial, inicial),
        rebanho_medio_cab=no_periodo["rebanho_medio_cab"], rebanho_medio_ua=no_periodo["rebanho_medio_ua"],
        lotacao_cab_ha=no_periodo["lotacao_cab_ha"], lotacao_ua_ha=no_periodo["lotacao_ua_ha"],
        lotacao_cab_ha_prevista=prevista, lotacao_maxima=max(lotacoes, default=None),
        lotacao_minima=min(lotacoes, default=None), meses=meses, leitura=[])
    secao.leitura = leitura_da_lotacao(recortes, secao)
    return secao


def rebanho_e_area_por_mes(s: Session, recortes: Recortes) -> tuple[dict[date, DoMes], dict[date, DoMes]]:
    """(realizado, previsto): mês -> rebanho médio (cab e UA informada) e área, no período inteiro."""
    por_cenario: dict[str, dict[date, DoMes]] = {"realizado": defaultdict(DoMes), "planejado": defaultdict(DoMes)}
    parametros = recortes.periodo.parametros()
    for linha in s.execute(text(REBANHO_POR_MES), parametros).mappings():
        do_mes = por_cenario[linha["cenario"]][linha["competencia"]]
        do_mes.cabecas = float(linha["cabecas"] or 0)
        if linha["ua"] is not None:
            do_mes.ua = float(linha["ua"])
    for linha in s.execute(text(AREA_POR_MES), parametros).mappings():
        por_cenario[linha["cenario"]][linha["competencia"]].area = float(linha["area"] or 0)
    return por_cenario["realizado"], por_cenario["planejado"]


def meses_da_lotacao(recortes: Recortes, realizado: dict[date, DoMes],
                     previsto: dict[date, DoMes]) -> list[MesDaLotacao]:
    meses = []
    for mes in recortes.meses_do_periodo():
        prevista = dividir(previsto[mes].cabecas, previsto[mes].area) if mes in previsto else None
        if mes > recortes.mes_referencia or mes not in realizado:
            meses.append(MesDaLotacao(mes=mes, rebanho_medio_cab=None, rebanho_medio_ua=None, area_ha=None,
                                      lotacao_cab_ha=None, lotacao_ua_ha=None, lotacao_cab_ha_prevista=prevista))
            continue
        do_mes = realizado[mes]
        meses.append(MesDaLotacao(mes=mes, rebanho_medio_cab=do_mes.cabecas, rebanho_medio_ua=do_mes.ua,
                                  area_ha=do_mes.area or None, lotacao_cab_ha=dividir(do_mes.cabecas, do_mes.area),
                                  lotacao_ua_ha=dividir(do_mes.ua, do_mes.area),
                                  lotacao_cab_ha_prevista=prevista))
    return meses


def lotacao_prevista(recortes: Recortes, previsto: dict[date, DoMes]) -> float | None:
    """Σ cabeças previstas ÷ Σ área prevista, dos meses até o de referência em que o plano tem área (a mesma regra
    do placar, `rebanho_e_lotacao_previstos`)."""
    cabecas = 0.0
    area = 0.0
    for mes in recortes.meses_ate_a_referencia():
        if mes in previsto and previsto[mes].area:
            cabecas += previsto[mes].cabecas
            area += previsto[mes].area
    return dividir(cabecas, area)


def leitura_da_lotacao(recortes: Recortes, secao: SecaoLotacao) -> list[str]:
    mes = textos.mes_por_extenso(recortes.mes_referencia)
    if secao.rebanho_medio_cab is None:
        return [f"Não há rebanho médio informado no período (até {mes}); sem ele não há lotação."]
    frases = [f"O rebanho médio do período até {mes} foi de {textos.cabecas(secao.rebanho_medio_cab)}."]
    if secao.lotacao_cab_ha is None:
        frases.append("A fazenda não tem área de pasto informada no período; por isso a lotação fica em branco.")
        return frases
    frase = f"A lotação média até {mes} é de {textos.numero(secao.lotacao_cab_ha, 2)} cab/ha"
    if secao.lotacao_ua_ha is not None:
        frase += f" ({textos.numero(secao.lotacao_ua_ha, 2)} UA/ha)"
    if secao.lotacao_cab_ha_prevista:
        variacao = dividir(secao.lotacao_cab_ha - secao.lotacao_cab_ha_prevista, secao.lotacao_cab_ha_prevista)
        frase += (f", {textos.frente_ao_previsto(variacao, feminino=True)} "
                  f"({textos.numero(secao.lotacao_cab_ha_prevista, 2)} cab/ha)")
    frases.append(frase + ".")
    extremos = mes_de_maior_e_menor_lotacao(secao.meses)
    if extremos is not None:
        maior, menor = extremos
        frases.append(frase_dos_extremos(maior, menor))
    return frases


def frase_dos_extremos(maior: MesDaLotacao, menor: MesDaLotacao) -> str:
    maxima = textos.numero(maior.lotacao_cab_ha, 2)
    minima = textos.numero(menor.lotacao_cab_ha, 2)
    if maxima == minima:
        return f"A lotação ficou em {maxima} cab/ha em todos os meses com área."
    return (f"A maior lotação foi em {textos.mes_por_extenso(maior.mes)} ({maxima} cab/ha) e a menor em "
            f"{textos.mes_por_extenso(menor.mes)} ({minima} cab/ha).")


def mes_de_maior_e_menor_lotacao(meses: list[MesDaLotacao]) -> tuple[MesDaLotacao, MesDaLotacao] | None:
    com_lotacao = [mes for mes in meses if mes.lotacao_cab_ha is not None]
    if len(com_lotacao) < 2:
        return None
    maior = max(com_lotacao, key=lambda mes: mes.lotacao_cab_ha)
    menor = min(com_lotacao, key=lambda mes: mes.lotacao_cab_ha)
    return maior, menor
