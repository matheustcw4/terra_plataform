"""A folha 01 do boletim de resultados (o modo Analítico do PDF): o que só ela mostra, já somado.

- Vendas: as cabeças de abate e em pé juntas, no acumulado contra o previsto; compras: as compradas.
- Desembolso por grupo: os sete maiores centros de custo do acumulado e o resto somado em "Outros (N grupos)".
- Resultado: verde quando o realizado é maior ou igual ao planejado, vermelho abaixo (a regra do gerador oficial do
  boletim da Terra). O semáforo do BI compara pelo %, e com o planejado negativo um resultado melhor sairia vermelho.
"""

from app.kpis.analitico.comparar import comparado
from app.kpis.analitico.placar import DoRecorte, TresRecortes
from app.schemas.analitico import CentroDoDesembolso, ParteDoDesembolso, SecaoCaixa, SecaoFinanceiro, SecaoResumo
from app.schemas.api import Comparacao

GRUPOS_NO_RESUMO = 7


def secao_resumo(valores: TresRecortes, financeiro: SecaoFinanceiro, caixa: SecaoCaixa, limiar: float) -> SecaoResumo:
    acumulado = valores.acumulado
    previstas, vendidas = cabecas_vendidas(acumulado)
    resultado = caixa.previsto_realizado.resultado
    return SecaoResumo(
        vendas=comparado(previstas, vendidas, "maior_melhor", limiar),
        compras=comparado(acumulado.compras.planejado.cabecas, acumulado.compras.realizado.cabecas, None, limiar),
        desembolso_por_grupo=grupos_do_resumo(financeiro.centros),
        desembolso_total=sum(centro.valor_acumulado for centro in financeiro.centros),
        status_do_resultado_mes=status_do_resultado(resultado.mensal),
        status_do_resultado_acumulado=status_do_resultado(resultado.acumulado))


def cabecas_vendidas(recorte: DoRecorte) -> tuple[float, float]:
    """(previstas, vendidas): abate e em pé juntos."""
    previstas = recorte.abate.planejado.cabecas + recorte.em_pe.planejado.cabecas
    vendidas = recorte.abate.realizado.cabecas + recorte.em_pe.realizado.cabecas
    return previstas, vendidas


def grupos_do_resumo(centros: list[CentroDoDesembolso]) -> list[ParteDoDesembolso]:
    """Os maiores centros de custo e o resto numa linha só; um único centro a mais entra com o próprio nome."""
    mostrados = centros[:GRUPOS_NO_RESUMO]
    resto = centros[GRUPOS_NO_RESUMO:]
    if len(resto) == 1:
        mostrados = centros
        resto = []
    partes = [ParteDoDesembolso(nome=centro.centro_custo, valor=centro.valor_acumulado) for centro in mostrados]
    if resto:
        partes.append(ParteDoDesembolso(nome=f"Outros ({len(resto)} grupos)",
                                        valor=sum(centro.valor_acumulado for centro in resto)))
    return partes


def status_do_resultado(comparacao: Comparacao) -> str | None:
    if comparacao.realizado == 0 and comparacao.planejado == 0:
        return None
    if comparacao.realizado >= comparacao.planejado:
        return "verde"
    return "vermelho"
