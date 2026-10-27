"""Movimentações de gado somadas por recorte (sexo ou grupo) e cenário, e os indicadores de lote (compra, venda,
transferência) que as páginas mostram. Tudo sai de `fato.mov_animal`, sob o RLS de quem pede.

Regras (as mesmas medidas DAX dos dois BIs: docs/analises/01 §5.6–5.10 e 02 §4.4–4.5):
- arroba do abate = kg de carcaça ÷ 15; da venda em pé, da compra e da transferência = kg vivo ÷ 30 (rendimento
  implícito de 50%, P11);
- preço da @ = valor ÷ arrobas; preço do kg = valor ÷ kg vivo; peso médio = kg vivo ÷ cabeças;
- rendimento de carcaça = kg de carcaça ÷ kg vivo (só no abate);
- GERAL soma tudo, inclusive categoria ainda sem de-para (nada some do total); MACHO/FÊMEA (sexo) e
  BEZERROS/JOVENS/ADULTOS (grupo) vêm da categoria BI;
- planejado = cenário 'planejado' (as metas da planilha);
- acumulado = soma do realizado do início do período até o mês (P3: um único conceito de acumulado).
"""

from dataclasses import dataclass
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.filtro import Filtro, meses_do_filtro
from app.schemas.api import IndicadoresDoLote, MesDaContagem, MesDoLote, QuadroDoLote


@dataclass(frozen=True)
class TipoDeLote:
    tipo_no_fato: str              # valor de fato.mov_animal.tipo
    kg_por_arroba: int
    arroba_pela_carcaca: bool      # abate: @ de carcaça; os demais: @ calculada sobre o peso vivo


ABATE = TipoDeLote(tipo_no_fato="ABATE", kg_por_arroba=15, arroba_pela_carcaca=True)
VENDA_EM_PE = TipoDeLote(tipo_no_fato="VENDA_EM_PE", kg_por_arroba=30, arroba_pela_carcaca=False)
COMPRA = TipoDeLote(tipo_no_fato="COMPRA", kg_por_arroba=30, arroba_pela_carcaca=False)
TRANSF_ENTRADA = TipoDeLote(tipo_no_fato="TRANSF_ENTRADA", kg_por_arroba=30, arroba_pela_carcaca=False)
TRANSF_SAIDA = TipoDeLote(tipo_no_fato="TRANSF_SAIDA", kg_por_arroba=30, arroba_pela_carcaca=False)

# recorte -> quadros da página, nessa ordem; a chave é também a coluna de dim.categoria_bi
RECORTES = {"sexo": ["GERAL", "MACHO", "FÊMEA"], "grupo": ["GERAL", "BEZERROS", "JOVENS", "ADULTOS"]}
CENARIOS = ["realizado", "planejado"]

# TODO(D7): com mais de uma versão de plano por fazenda, o planejado terá de escolher a versão ativa. Hoje cada
# fazenda tem uma só (a da planilha).
TOTAIS_POR_RECORTE = """
    SELECT m.cenario, b.{coluna} AS recorte, sum(m.qtd) AS cabecas, sum(m.valor_total) AS valor,
           sum(m.peso_vivo_total_kg) AS kg_vivo, sum(m.peso_carcaca_total_kg) AS kg_carcaca
    FROM fato.mov_animal m
    LEFT JOIN dim.categoria_map c ON c.id = m.categoria_map_id
    LEFT JOIN dim.categoria_bi b ON b.id = c.categoria_bi_id
    WHERE m.tipo = :tipo AND m.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND m.competencia = ANY (CAST(:meses AS date[]))
    GROUP BY m.cenario, b.{coluna}
"""
TOTAIS_POR_MES = """
    SELECT m.competencia, m.cenario, sum(m.qtd) AS cabecas, sum(m.valor_total) AS valor,
           sum(m.peso_vivo_total_kg) AS kg_vivo, sum(m.peso_carcaca_total_kg) AS kg_carcaca
    FROM fato.mov_animal m
    WHERE m.tipo = :tipo AND m.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND m.competencia = ANY (CAST(:meses AS date[]))
    GROUP BY m.competencia, m.cenario
"""


@dataclass
class Somas:
    cabecas: float = 0.0
    valor: float = 0.0
    kg_vivo: float = 0.0
    kg_carcaca: float = 0.0

    def somar(self, linha) -> None:
        self.cabecas += numero(linha, "cabecas")
        self.valor += numero(linha, "valor")
        self.kg_vivo += numero(linha, "kg_vivo")
        self.kg_carcaca += numero(linha, "kg_carcaca")


def parametros(filtro: Filtro, tipo_no_fato: str) -> dict:
    resultado = filtro.parametros()
    resultado["tipo"] = tipo_no_fato
    return resultado


def somas_por_recorte(s: Session, filtro: Filtro, tipo_no_fato: str,
                      por: str = "sexo") -> dict[tuple[str, str], Somas]:
    """(cenário, recorte) -> somas. GERAL leva toda linha; os outros recortes, só a da categoria daquele sexo ou
    grupo. `por` vem de RECORTES (lista fechada), nunca do pedido: por isso pode entrar no SQL."""
    somas = {}
    for cenario in CENARIOS:
        for recorte in RECORTES[por]:
            somas[(cenario, recorte)] = Somas()
    sql = TOTAIS_POR_RECORTE.format(coluna=por)
    for linha in s.execute(text(sql), parametros(filtro, tipo_no_fato)).mappings():
        somas[(linha["cenario"], "GERAL")].somar(linha)
        if (linha["cenario"], linha["recorte"]) in somas:
            somas[(linha["cenario"], linha["recorte"])].somar(linha)
    return somas


def somas_por_mes(s: Session, filtro: Filtro, tipo_no_fato: str) -> dict[tuple[date, str], Somas]:
    """(mês, cenário) -> somas."""
    somas: dict[tuple[date, str], Somas] = {}
    for linha in s.execute(text(TOTAIS_POR_MES), parametros(filtro, tipo_no_fato)).mappings():
        do_mes = Somas()
        do_mes.somar(linha)
        somas[(linha["competencia"], linha["cenario"])] = do_mes
    return somas


def quadro(s: Session, filtro: Filtro, tipo: TipoDeLote) -> list[QuadroDoLote]:
    """Os quadros GERAL, MACHO e FÊMEA, cada um com o realizado e o planejado."""
    somas = somas_por_recorte(s, filtro, tipo.tipo_no_fato)
    quadros = []
    for recorte in RECORTES["sexo"]:
        quadros.append(QuadroDoLote(recorte=recorte, realizado=indicadores(somas[("realizado", recorte)], tipo),
                                    planejado=indicadores(somas[("planejado", recorte)], tipo)))
    return quadros


def indicadores(somas: Somas, tipo: TipoDeLote) -> IndicadoresDoLote:
    if tipo.arroba_pela_carcaca:
        arrobas = somas.kg_carcaca / tipo.kg_por_arroba
        rendimento = dividir(somas.kg_carcaca, somas.kg_vivo)
    else:
        arrobas = somas.kg_vivo / tipo.kg_por_arroba
        rendimento = None
    return IndicadoresDoLote(cabecas=somas.cabecas, valor=somas.valor, kg_vivo=somas.kg_vivo, arrobas=arrobas,
                             preco_arroba=dividir(somas.valor, arrobas), preco_kg=dividir(somas.valor, somas.kg_vivo),
                             peso_medio_kg=dividir(somas.kg_vivo, somas.cabecas), rendimento_carcaca=rendimento)


def serie_mensal(s: Session, filtro: Filtro, tipo: TipoDeLote) -> list[MesDoLote]:
    somas = somas_por_mes(s, filtro, tipo.tipo_no_fato)
    serie = []
    acumulado = 0.0
    for mes in meses_do_filtro(filtro):
        realizado = somas.get((mes, "realizado"), Somas())
        planejado = somas.get((mes, "planejado"), Somas())
        acumulado += realizado.cabecas
        serie.append(MesDoLote(mes=mes, cabecas=realizado.cabecas, cabecas_planejadas=planejado.cabecas,
                               cabecas_acumuladas=acumulado, valor=realizado.valor, valor_planejado=planejado.valor,
                               preco_arroba=indicadores(realizado, tipo).preco_arroba))
    return serie


def serie_de_contagem(s: Session, filtro: Filtro, tipo_no_fato: str) -> list[MesDaContagem]:
    """Cabeças por mês, realizado e planejado, com os dois acumulados (os gráficos de nascimentos e de mortes)."""
    somas = somas_por_mes(s, filtro, tipo_no_fato)
    serie = []
    realizado_acumulado = 0.0
    planejado_acumulado = 0.0
    for mes in meses_do_filtro(filtro):
        realizado = somas.get((mes, "realizado"), Somas()).cabecas
        planejado = somas.get((mes, "planejado"), Somas()).cabecas
        realizado_acumulado += realizado
        planejado_acumulado += planejado
        serie.append(MesDaContagem(mes=mes, realizado=realizado, planejado=planejado,
                                   realizado_acumulado=realizado_acumulado, planejado_acumulado=planejado_acumulado))
    return serie


def dividir(numerador: float, denominador: float | None) -> float | None:
    """Sem base (zero ou vazio) não existe razão: o card mostra traço, e não um 0 que parece resultado."""
    if not denominador:
        return None
    return numerador / denominador


def numero(linha, campo: str) -> float:
    """Valor somado no SQL; soma de nulos (peso ou valor não informado) conta como zero."""
    if linha[campo] is None:
        return 0.0
    return float(linha[campo])
