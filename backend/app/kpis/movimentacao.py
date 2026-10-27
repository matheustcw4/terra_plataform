"""KPIs da página Movimentação do Gado, a mesma página do BI de planilhas (docs/analises/01 §7.5).

Cartões e gráficos (as medidas DAX do BI, docs/referencias/pbix_ciclo/dax_measures.csv):
- estoque final = saldo acumulado até o último mês ("Stock Accumulated Final"), de `fato.estoque_mensal`;
- rebanho médio = Σ do rebanho médio mensal ÷ nº de meses com rebanho > 0, em cabeças e em UA ("Mean Month",
  "UA Median Month"); lotação = Σ cabeças (ou UA) ÷ Σ área dos mesmos meses ("Mean Month Ha", "UA Median Ha").
  O BI conta os meses pelo número do mês, sem o ano (bug P2): acima de 12 meses ele erra e aqui não;
- nascimentos, mortes, compras e vendas (abate + em pé) = cabeças no período, com o planejado e o % da meta
  (realizado ÷ planejado); índice de mortalidade = mortes ÷ rebanho médio ("% mORTALITY ( MEAN MONTH)");
- estoque final mês a mês e estoque final por categoria BI.
Categoria de origem ainda sem categoria BI fica fora do estoque e do rebanho médio (pendência de mapeamento), mas
entra nas contagens de nascimentos, mortes, compras e vendas, como no BI.
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.filtro import Filtro, periodo_do_filtro
from app.schemas.api import ComMeta, EstoqueDaCategoria, EstoqueDoMes, Movimentacao

# cartão da página -> tipos de movimentação somados nele
CONTAGENS = {
    "nascimentos": ["NASCIMENTO"],
    "mortes": ["MORTE"],
    "compras": ["COMPRA"],
    "vendas": ["ABATE", "VENDA_EM_PE"],
}


def movimentacao(s: Session, filtro: Filtro) -> Movimentacao:
    rebanho = rebanho_e_area(s, filtro)
    contagens = contagens_com_meta(s, filtro)
    indice_mortalidade = dividir(contagens["mortes"].realizado, rebanho["rebanho_medio_cab"])
    return Movimentacao(
        periodo=periodo_do_filtro(filtro),
        estoque_final=estoque_final(s, filtro), rebanho_medio_cab=rebanho["rebanho_medio_cab"],
        rebanho_medio_ua=rebanho["rebanho_medio_ua"], lotacao_cab_ha=rebanho["lotacao_cab_ha"],
        lotacao_ua_ha=rebanho["lotacao_ua_ha"], nascimentos=contagens["nascimentos"], mortes=contagens["mortes"],
        indice_mortalidade=indice_mortalidade, compras=contagens["compras"], vendas=contagens["vendas"],
        estoque_mensal=estoque_mensal(s, filtro), estoque_por_categoria=estoque_por_categoria(s, filtro))


# --- estoque -------------------------------------------------------------------------------------------------------

# Último saldo de cada (fazenda, categoria) até o fim do período. `estoque_mensal` repete o saldo nos meses sem
# evento, então o último mês ≤ fim é o saldo no fim.
SALDO_NO_FIM = """
    SELECT DISTINCT ON (e.fazenda_id, e.categoria_bi_id) e.categoria_bi_id, e.saldo_final
    FROM fato.estoque_mensal e
    WHERE e.cenario = 'realizado' AND e.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND e.competencia <= :fim
    ORDER BY e.fazenda_id, e.categoria_bi_id, e.competencia DESC
"""
ESTOQUE_POR_CATEGORIA = f"""
    SELECT b.nome, sum(saldo.saldo_final) AS estoque_final
    FROM ({SALDO_NO_FIM}) saldo
    JOIN dim.categoria_bi b ON b.id = saldo.categoria_bi_id
    GROUP BY b.id, b.nome
    HAVING sum(saldo.saldo_final) <> 0
    ORDER BY b.id
"""
ESTOQUE_MENSAL = """
    SELECT e.competencia, sum(e.saldo_final) AS estoque_final
    FROM fato.estoque_mensal e
    WHERE e.cenario = 'realizado' AND e.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND e.competencia = ANY (CAST(:meses AS date[]))
    GROUP BY e.competencia
    ORDER BY e.competencia
"""


def estoque_por_categoria(s: Session, filtro: Filtro) -> list[EstoqueDaCategoria]:
    categorias = []
    for nome, saldo in s.execute(text(ESTOQUE_POR_CATEGORIA), filtro.parametros()):
        categorias.append(EstoqueDaCategoria(categoria=nome, estoque_final=float(saldo)))
    return categorias


def estoque_final(s: Session, filtro: Filtro) -> float:
    total = s.scalar(text(f"SELECT sum(saldo_final) FROM ({SALDO_NO_FIM}) saldo"), filtro.parametros())
    return float(total or 0)


def estoque_mensal(s: Session, filtro: Filtro) -> list[EstoqueDoMes]:
    meses = []
    for mes, saldo in s.execute(text(ESTOQUE_MENSAL), filtro.parametros()):
        meses.append(EstoqueDoMes(mes=mes, estoque_final=float(saldo)))
    return meses


# --- nascimentos, mortes, compras e vendas -------------------------------------------------------------------------

# TODO(D7): com mais de uma versão de plano por fazenda, o planejado terá de escolher a versão ativa. Hoje cada
# fazenda tem uma só (a da planilha).
CABECAS_POR_TIPO = """
    SELECT m.tipo, m.cenario, sum(m.qtd) AS cabecas
    FROM fato.mov_animal m
    WHERE m.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND m.competencia = ANY (CAST(:meses AS date[]))
      AND m.tipo IN ('NASCIMENTO', 'MORTE', 'COMPRA', 'ABATE', 'VENDA_EM_PE')
    GROUP BY m.tipo, m.cenario
"""


def contagens_com_meta(s: Session, filtro: Filtro) -> dict[str, ComMeta]:
    cabecas: dict[tuple[str, str], float] = {}
    for tipo, cenario, quantidade in s.execute(text(CABECAS_POR_TIPO), filtro.parametros()):
        cabecas[(tipo, cenario)] = float(quantidade)
    resultado = {}
    for cartao, tipos in CONTAGENS.items():
        realizado = sum(cabecas.get((tipo, "realizado"), 0.0) for tipo in tipos)
        planejado = sum(cabecas.get((tipo, "planejado"), 0.0) for tipo in tipos)
        resultado[cartao] = ComMeta(realizado=realizado, planejado=planejado,
                                    percentual_da_meta=dividir(realizado, planejado))
    return resultado


# --- rebanho médio e lotação ---------------------------------------------------------------------------------------

REBANHO_POR_MES = """
    SELECT r.competencia, sum(r.qtd_cab) AS cabecas, sum(r.qtd_ua_informada) AS ua
    FROM fato.rebanho_medio_mensal r
    LEFT JOIN dim.categoria_map m ON m.id = r.categoria_map_id
    WHERE r.cenario = 'realizado' AND r.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND r.competencia = ANY (CAST(:meses AS date[]))
      AND (r.categoria_map_id IS NULL OR m.categoria_bi_id IS NOT NULL)    -- categoria pendente fica fora
    GROUP BY r.competencia
"""
AREA_DO_PERIODO = """
    SELECT sum(a.area_total_ha)
    FROM fato.area_mensal a
    WHERE a.cenario = 'realizado' AND a.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND a.competencia = ANY (CAST(:meses AS date[]))
"""


def rebanho_e_area(s: Session, filtro: Filtro) -> dict[str, float | None]:
    """Rebanho médio (cab e UA) e lotação. Sem mês com rebanho, tudo fica vazio; sem UA informada, só a UA."""
    total_cabecas = 0.0
    total_ua = 0.0
    tem_ua = False
    meses_com_rebanho = 0
    for _, cabecas, ua in s.execute(text(REBANHO_POR_MES), filtro.parametros()):
        total_cabecas += float(cabecas)
        if cabecas > 0:
            meses_com_rebanho += 1
        if ua is not None:
            total_ua += float(ua)
            tem_ua = True
    vazio: dict[str, float | None] = {"rebanho_medio_cab": None, "rebanho_medio_ua": None, "lotacao_cab_ha": None,
                                      "lotacao_ua_ha": None}
    if meses_com_rebanho == 0:
        return vazio
    area_total = float(s.scalar(text(AREA_DO_PERIODO), filtro.parametros()) or 0)
    resultado = dict(vazio)
    resultado["rebanho_medio_cab"] = total_cabecas / meses_com_rebanho
    resultado["lotacao_cab_ha"] = dividir(total_cabecas, area_total)
    if tem_ua:
        resultado["rebanho_medio_ua"] = total_ua / meses_com_rebanho
        resultado["lotacao_ua_ha"] = dividir(total_ua, area_total)
    return resultado


def dividir(numerador: float, denominador: float | None) -> float | None:
    """Sem base (zero ou vazio) não há razão: o cartão mostra traço, e não um 0 que parece resultado."""
    if not denominador:
        return None
    return numerador / denominador
