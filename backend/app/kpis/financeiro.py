"""KPIs da página Financeiro, a mesma do BI de planilhas (docs/analises/01 §5.11, §5.12 e §7.4): o desembolso e as
receitas do período, os velocímetros de desembolso e de custeio por cabeça por mês e do preço da @ vendida, o
desembolso por centro de custo e os gráficos mês a mês (fluxo de caixa, receitas, desembolso e desembolso por cabeça,
realizado × planejado).

Regras:
- a classificação de cada conta (desembolso, custeio, receita) vem de `dim.centro_custo` (doc 01 §5.5), nunca das
  colunas DESEMBOLSO/CUSTEIO da planilha; onde a planilha classifica diferente, o número diverge do BI (P4);
- desembolso (DCM) e custeio (CCM) = débitos − créditos nas contas marcadas: crédito em conta de despesa é estorno e
  abate a despesa, como o valor negativo que o BI soma ("Outlay", "Costing");
- receitas = créditos das contas de receita da pecuária e da agricultura ("Revenues");
- despesas do fluxo de caixa = todos os débitos, menos os estornos das contas de despesa ("Expenses Graph");
  saldo = todas as receitas, inclusive as outras (arrendamento, vendas de outros animais...), − despesas ("Balance":
  o BI soma as outras receitas na linha e não na barra, docs/analises/01 §8.1, item 7);
- por cabeça por mês = valor do período ÷ Σ do rebanho médio de cada mês, o mesmo que valor ÷ rebanho médio ÷ nº de
  meses ("head outlay accumulated", "Costing head Accumulated"); o planejado usa o rebanho planejado;
- fim da escala dos velocímetros = meta × fator de `dim.parametro`, como o BI; o custeio usa o fator do desembolso,
  porque o BI não fixa a escala dele.
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.compras import preco_da_arroba_vendida
from app.kpis.filtro import Filtro, meses_do_filtro, periodo_do_filtro
from app.kpis.lotes import dividir, numero
from app.kpis.previsto_financeiro import (
    ORCAMENTO_ESCOLHIDO,
    PEDIDO_PADRAO,
    PedidoDoPrevisto,
    PrevistoEscolhido,
    escolher_o_previsto,
)
from app.schemas.api import DesembolsoDoCentro, Financeiro, MesDoFinanceiro, Velocimetro

# cenário -> view com a classificação da conta já resolvida (lista fechada: por isso pode entrar no SQL); no
# planejado, o orçamento do tipo e da versão escolhidos na tela (previsto_financeiro.py)
VIEW_DO_CENARIO = {"realizado": "fato.v_lancamento_financeiro", "planejado": ORCAMENTO_ESCOLHIDO}

# TODO(D3): as marcas de desembolso e custeio de cada centro estão em dim.centro_custo, à espera da decisão D3.
TOTAIS_POR_MES = """
    SELECT v.competencia,
           sum(v.valor) FILTER (WHERE v.natureza = 'C' AND v.tipo_custeio IN ('RECEITA_PEC', 'RECEITA_AGR'))
               AS receitas,
           sum(v.valor) FILTER (WHERE v.natureza = 'C' AND v.tipo_custeio = 'RECEITA_OUTRAS') AS outras_receitas,
           sum(CASE v.natureza WHEN 'D' THEN v.valor ELSE -v.valor END)
               FILTER (WHERE v.natureza = 'D' OR v.entra_desembolso OR v.entra_custeio) AS despesas,
           sum(CASE v.natureza WHEN 'D' THEN v.valor ELSE -v.valor END) FILTER (WHERE v.entra_desembolso)
               AS desembolso,
           sum(CASE v.natureza WHEN 'D' THEN v.valor ELSE -v.valor END) FILTER (WHERE v.entra_custeio) AS custeio
    FROM {view} v
    WHERE v.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND v.competencia = ANY (CAST(:meses AS date[]))
    GROUP BY v.competencia
"""
REBANHO_POR_MES = """
    SELECT r.competencia, r.cenario, sum(r.qtd_cab) AS cabecas
    FROM fato.rebanho_medio_mensal r
    LEFT JOIN dim.categoria_map m ON m.id = r.categoria_map_id
    WHERE r.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND r.competencia = ANY (CAST(:meses AS date[]))
      AND (r.categoria_map_id IS NULL OR m.categoria_bi_id IS NOT NULL)    -- categoria pendente fica fora
    GROUP BY r.competencia, r.cenario
"""
DESEMBOLSO_POR_CENTRO = """
    SELECT v.centro_custo, sum(CASE v.natureza WHEN 'D' THEN v.valor ELSE -v.valor END) AS valor
    FROM fato.v_lancamento_financeiro v
    WHERE (v.entra_desembolso OR v.eh_reposicao)
      AND v.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND v.competencia = ANY (CAST(:meses AS date[]))
    GROUP BY v.centro_custo
    HAVING sum(CASE v.natureza WHEN 'D' THEN v.valor ELSE -v.valor END) <> 0
    ORDER BY 2 DESC, 1
"""
FATOR = "SELECT valor FROM dim.parametro WHERE chave = :chave"


@dataclass
class Valores:
    """Os totais de um mês (ou do período) num cenário."""
    receitas: float = 0.0
    outras_receitas: float = 0.0
    despesas: float = 0.0
    desembolso: float = 0.0
    custeio: float = 0.0
    cabecas: float = 0.0            # rebanho médio do mês; no período, a soma dos meses

    def somar(self, outro: "Valores") -> None:
        self.receitas += outro.receitas
        self.outras_receitas += outro.outras_receitas
        self.despesas += outro.despesas
        self.desembolso += outro.desembolso
        self.custeio += outro.custeio
        self.cabecas += outro.cabecas


def financeiro(s: Session, filtro: Filtro, pedido: PedidoDoPrevisto = PEDIDO_PADRAO) -> Financeiro:
    previsto = escolher_o_previsto(s, filtro, pedido)
    realizado = valores_por_mes(s, filtro, "realizado")
    planejado = valores_por_mes(s, filtro, "planejado", previsto)
    no_periodo = somar_meses(realizado)
    meta = somar_meses(planejado)
    fator_de_custo = fator(s, "multiplicador_gauge_desembolso")
    preco = velocimetro(preco_da_arroba_vendida(s, filtro), preco_da_arroba_vendida(s, filtro, "planejado"),
                        fator(s, "multiplicador_gauge_preco"), maior_e_melhor=True)
    return Financeiro(
        periodo=periodo_do_filtro(filtro), desembolso=no_periodo.desembolso, receitas=no_periodo.receitas,
        desembolso_por_cabeca_mes=velocimetro(dividir(no_periodo.desembolso, no_periodo.cabecas),
                                              dividir(meta.desembolso, meta.cabecas), fator_de_custo,
                                              maior_e_melhor=False),
        custeio_por_cabeca_mes=velocimetro(dividir(no_periodo.custeio, no_periodo.cabecas),
                                           dividir(meta.custeio, meta.cabecas), fator_de_custo, maior_e_melhor=False),
        preco_arroba_venda=preco, desembolso_por_centro=desembolso_por_centro(s, filtro),
        serie_mensal=serie_mensal(filtro, realizado, planejado), previsto=previsto.opcoes)


def valores_por_mes(s: Session, filtro: Filtro, cenario: str, previsto: PrevistoEscolhido | None = None
                    ) -> dict[date, Valores]:
    """Mês -> totais do cenário: o dinheiro (lançamentos ou orçamento) e o rebanho médio. No planejado sem
    escolha, vale a escolha padrão do orçamento."""
    if cenario == "planejado" and previsto is None:
        previsto = escolher_o_previsto(s, filtro, PEDIDO_PADRAO)
    parametros = filtro.parametros()
    if previsto is not None:
        parametros = parametros | previsto.parametros()
    valores: dict[date, Valores] = {}
    sql = TOTAIS_POR_MES.format(view=VIEW_DO_CENARIO[cenario])
    for linha in s.execute(text(sql), parametros).mappings():
        valores[linha["competencia"]] = Valores(
            receitas=numero(linha, "receitas"), outras_receitas=numero(linha, "outras_receitas"),
            despesas=numero(linha, "despesas"), desembolso=numero(linha, "desembolso"),
            custeio=numero(linha, "custeio"))
    for linha in s.execute(text(REBANHO_POR_MES), filtro.parametros()).mappings():
        if linha["cenario"] != cenario:
            continue
        if linha["competencia"] not in valores:
            valores[linha["competencia"]] = Valores()
        valores[linha["competencia"]].cabecas = numero(linha, "cabecas")
    return valores


def somar_meses(valores: dict[date, Valores]) -> Valores:
    total = Valores()
    for do_mes in valores.values():
        total.somar(do_mes)
    return total


def velocimetro(realizado: float | None, planejado: float | None, fator_da_escala: float,
                maior_e_melhor: bool) -> Velocimetro:
    """`maior_e_melhor`: no preço da @, passar da meta é bom; no desembolso e no custeio, é ruim."""
    maximo = None
    if planejado is not None:
        maximo = planejado * fator_da_escala
    dentro_da_meta = None
    if realizado is not None and planejado is not None:
        if maior_e_melhor:
            dentro_da_meta = realizado >= planejado
        else:
            dentro_da_meta = realizado <= planejado
    return Velocimetro(realizado=realizado, planejado=planejado, maximo=maximo, dentro_da_meta=dentro_da_meta)


def fator(s: Session, chave: str) -> float:
    return float(s.scalar(text(FATOR), {"chave": chave}))


def desembolso_por_centro(s: Session, filtro: Filtro) -> list[DesembolsoDoCentro]:
    """"RELAÇÃO DESEMBOLSO TOTAL" do BI: desembolso e reposição de gado, por centro de custo."""
    centros = []
    for centro, valor in s.execute(text(DESEMBOLSO_POR_CENTRO), filtro.parametros()):
        centros.append(DesembolsoDoCentro(centro_custo=centro, valor=float(valor)))
    return centros


def serie_mensal(filtro: Filtro, realizado: dict[date, Valores],
                 planejado: dict[date, Valores]) -> list[MesDoFinanceiro]:
    serie = []
    for mes in meses_do_filtro(filtro):
        do_mes = realizado.get(mes, Valores())
        meta = planejado.get(mes, Valores())
        serie.append(MesDoFinanceiro(
            mes=mes, receitas=do_mes.receitas, receitas_planejadas=meta.receitas, despesas=do_mes.despesas,
            saldo=do_mes.receitas + do_mes.outras_receitas - do_mes.despesas, desembolso=do_mes.desembolso,
            desembolso_planejado=meta.desembolso, desembolso_por_cabeca=dividir(do_mes.desembolso, do_mes.cabecas),
            desembolso_por_cabeca_planejado=dividir(meta.desembolso, meta.cabecas)))
    return serie
