"""KPIs da página Nascimentos, a mesma do BI de planilhas: quadros Fêmea / Macho / Geral com os nascimentos
realizados e planejados; nos quadros de sexo, a participação no total ("IN - % Female Birth" / "% Male Birth"), e no
geral, o % da meta ("% Birth x Forecast"); gráficos mensal e acumulado, realizado × planejado.

O sexo vem da categoria BI do nascimento. O acumulado começa no início do período escolhido (P3); o BI acumula desde
janeiro, ou desde sempre quando o período pega dois anos civis.
"""

from sqlalchemy.orm import Session

from app.kpis import lotes
from app.kpis.filtro import Filtro, periodo_do_filtro
from app.schemas.api import Nascimentos, NascimentosDoSexo

TIPO = "NASCIMENTO"


def nascimentos(s: Session, filtro: Filtro) -> Nascimentos:
    somas = lotes.somas_por_recorte(s, filtro, TIPO)
    total = somas[("realizado", "GERAL")].cabecas
    quadro = []
    for recorte in lotes.RECORTES["sexo"]:
        realizado = somas[("realizado", recorte)].cabecas
        planejado = somas[("planejado", recorte)].cabecas
        quadro.append(NascimentosDoSexo(recorte=recorte, realizado=realizado, planejado=planejado,
                                        percentual_da_meta=lotes.dividir(realizado, planejado),
                                        participacao_no_total=lotes.dividir(realizado, total)))
    return Nascimentos(periodo=periodo_do_filtro(filtro), quadro=quadro,
                       serie_mensal=lotes.serie_de_contagem(s, filtro, TIPO))
