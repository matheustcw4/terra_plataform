"""KPIs da página Mortes, a mesma do BI de planilhas: quadros Bezerros / Jovens / Adultos / Geral com as mortes
realizadas, a mortalidade sobre o rebanho médio do grupo ("% mORTALITY ( MEAN MONTH)") e a meta; no quadro Bezerros,
também a mortalidade sobre os nascimentos ("% Mortality"); as mortes por causa e os gráficos mensal e acumulado.

Regras:
- o grupo vem da categoria BI; morte de categoria ainda sem de-para entra só no Geral (nada some do total);
- rebanho médio do grupo = Σ cabeças do grupo ÷ nº de meses em que o grupo teve rebanho, como o "Mean Month" do BI
  com o filtro de grupo do card; o Geral usa todos os grupos e é o mesmo rebanho médio da página Movimentação;
- mortalidade sobre os nascimentos = mortes de bezerros ÷ nascimentos do MESMO período (P3); o BI divide pelos
  nascimentos acumulados desde janeiro (ou desde sempre, quando o período pega dois anos civis);
- causa: o texto da fonte sem espaços nas pontas e em maiúsculas (o BI agrupa sem distinguir maiúsculas); sem causa
  vira "NÃO INFORMADO", o texto que as planilhas já usam (assim os dois somam na mesma barra).
"""

from collections import defaultdict
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.filtro import Filtro, periodo_do_filtro
from app.schemas.api import CausaDeMorte, Mortes, MortesDoGrupo

TIPO = "MORTE"

# Planilha informa o grupo; Metryx informa a categoria, e o grupo vem da dimensão. Categoria pendente fica fora.
REBANHO_POR_GRUPO = """
    SELECT r.competencia, coalesce(r.grupo, b.grupo) AS grupo, sum(r.qtd_cab) AS cabecas
    FROM fato.rebanho_medio_mensal r
    LEFT JOIN dim.categoria_map m ON m.id = r.categoria_map_id
    LEFT JOIN dim.categoria_bi b ON b.id = m.categoria_bi_id
    WHERE r.cenario = :cenario AND r.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND r.competencia = ANY (CAST(:meses AS date[]))
      AND (r.categoria_map_id IS NULL OR m.categoria_bi_id IS NOT NULL)
    GROUP BY r.competencia, coalesce(r.grupo, b.grupo)
"""
MORTES_POR_CAUSA = """
    SELECT coalesce(upper(nullif(btrim(m.causa), '')), 'NÃO INFORMADO') AS causa, sum(m.qtd) AS cabecas
    FROM fato.mov_animal m
    WHERE m.tipo = 'MORTE' AND m.cenario = 'realizado' AND m.fazenda_id = ANY (CAST(:fazendas AS uuid[]))
      AND m.competencia = ANY (CAST(:meses AS date[]))
    GROUP BY 1
    HAVING sum(m.qtd) > 0
    ORDER BY 2 DESC, 1
"""


def mortes(s: Session, filtro: Filtro) -> Mortes:
    somas = lotes.somas_por_recorte(s, filtro, TIPO, por="grupo")
    rebanho_medio = rebanho_medio_por_grupo(s, filtro)
    nascidos = lotes.somas_por_recorte(s, filtro, "NASCIMENTO")[("realizado", "GERAL")].cabecas
    quadro = []
    for recorte in lotes.RECORTES["grupo"]:
        realizado = somas[("realizado", recorte)].cabecas
        planejado = somas[("planejado", recorte)].cabecas
        sobre_nascimentos = None
        if recorte == "BEZERROS":
            sobre_nascimentos = lotes.dividir(realizado, nascidos)
        quadro.append(MortesDoGrupo(recorte=recorte, realizado=realizado, planejado=planejado,
                                    percentual_da_meta=lotes.dividir(realizado, planejado),
                                    sobre_rebanho_medio=lotes.dividir(realizado, rebanho_medio[recorte]),
                                    sobre_nascimentos=sobre_nascimentos))
    return Mortes(periodo=periodo_do_filtro(filtro), quadro=quadro, causas=mortes_por_causa(s, filtro),
                  serie_mensal=lotes.serie_de_contagem(s, filtro, TIPO))


def rebanho_medio_por_grupo(s: Session, filtro: Filtro, cenario: str = "realizado") -> dict[str, float | None]:
    """Recorte (GERAL e cada grupo) -> rebanho médio em cabeças; vazio quando o recorte não teve rebanho. O cenário
    planejado serve ao boletim analítico (mortalidade prevista por grupo)."""
    cabecas_por_mes: dict[tuple[str, date], float] = defaultdict(float)
    parametros = filtro.parametros()
    parametros["cenario"] = cenario
    for linha in s.execute(text(REBANHO_POR_GRUPO), parametros).mappings():
        cabecas = float(linha["cabecas"])
        cabecas_por_mes[(linha["grupo"], linha["competencia"])] += cabecas
        cabecas_por_mes[("GERAL", linha["competencia"])] += cabecas
    total: dict[str, float] = defaultdict(float)
    meses_com_rebanho: dict[str, int] = defaultdict(int)
    for (recorte, _), cabecas in cabecas_por_mes.items():
        total[recorte] += cabecas
        if cabecas > 0:
            meses_com_rebanho[recorte] += 1
    medias = {}
    for recorte in lotes.RECORTES["grupo"]:
        medias[recorte] = lotes.dividir(total[recorte], meses_com_rebanho[recorte])
    return medias


def mortes_por_causa(s: Session, filtro: Filtro) -> list[CausaDeMorte]:
    causas = []
    for causa, cabecas in s.execute(text(MORTES_POR_CAUSA), filtro.parametros()):
        causas.append(CausaDeMorte(causa=causa, cabecas=float(cabecas)))
    return causas
