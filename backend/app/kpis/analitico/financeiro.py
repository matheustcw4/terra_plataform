"""Placar financeiro e caixa do boletim analítico.

- Placar: receitas, desembolso, desembolso e custeio por cabeça por mês e preço da @ vendida, previsto × realizado
  no mês e no acumulado, e a meta do período (os mesmos números da página Financeiro, com os mesmos recortes).
- Desembolso por centro de custo: no mês e no acumulado, e por cabeça por mês no acumulado.
- Caixa: o Previsto × Realizado conta a conta (o mês de referência e o acumulado do período).
"""

from sqlalchemy.orm import Session

from app.kpis.analitico import textos
from app.kpis.analitico.comparar import Sentido, dividir, linha_do_placar
from app.kpis.analitico.recortes import Recortes
from app.kpis.financeiro import desembolso_por_centro, financeiro, somar_meses, valores_por_mes
from app.kpis.previsto_realizado import previsto_realizado
from app.schemas.analitico import CentroDoDesembolso, LinhaDoPlacar, SecaoCaixa, SecaoFinanceiro
from app.schemas.api import Financeiro, PrevistoRealizado


def previsto_e_realizado(financas: Financeiro, campo: str) -> tuple[float | None, float | None]:
    """(previsto, realizado) de um indicador da página Financeiro."""
    if campo == "receitas":
        return sum(mes.receitas_planejadas for mes in financas.serie_mensal), financas.receitas
    if campo == "desembolso":
        return sum(mes.desembolso_planejado for mes in financas.serie_mensal), financas.desembolso
    if campo == "saldo":
        return None, sum(mes.saldo for mes in financas.serie_mensal)
    velocimetro = getattr(financas, campo)
    return velocimetro.planejado, velocimetro.realizado


# (indicador, unidade, sentido, campo)
PLACAR = [
    ("Receitas", "R$", "maior_melhor", "receitas"),
    ("Desembolso", "R$", "menor_melhor", "desembolso"),
    ("Saldo do caixa", "R$", None, "saldo"),
    ("Desembolso por cabeça", "R$/cab/mês", "menor_melhor", "desembolso_por_cabeca_mes"),
    ("Custeio por cabeça", "R$/cab/mês", "menor_melhor", "custeio_por_cabeca_mes"),
    ("Preço da @ vendida", "R$/@", "maior_melhor", "preco_arroba_venda"),
]


def secao_financeiro(s: Session, recortes: Recortes, limiar: float) -> SecaoFinanceiro:
    mes = financeiro(s, recortes.mes)
    acumulado = financeiro(s, recortes.acumulado)
    periodo = financeiro(s, recortes.periodo)
    placar = []
    for nome, unidade, sentido, campo in PLACAR:
        placar.append(linha_financeira(nome, unidade, sentido, campo, (mes, acumulado, periodo), limiar))
    centros = centros_do_desembolso(s, recortes)
    leitura = leitura_financeira(recortes, placar, centros, sem_lancamento(acumulado))
    return SecaoFinanceiro(placar=placar, centros=centros, leitura=leitura)


def linha_financeira(nome: str, unidade: str, sentido: Sentido, campo: str,
                     recortes: tuple[Financeiro, Financeiro, Financeiro], limiar: float) -> LinhaDoPlacar:
    mes, acumulado, periodo = recortes
    meta, _ = previsto_e_realizado(periodo, campo)
    return linha_do_placar("FINANCEIRO", nome, unidade, sentido, previsto_e_realizado(mes, campo),
                           previsto_e_realizado(acumulado, campo), meta, limiar)


def centros_do_desembolso(s: Session, recortes: Recortes) -> list[CentroDoDesembolso]:
    do_mes = {centro.centro_custo: centro.valor for centro in desembolso_por_centro(s, recortes.mes)}
    rebanho_dos_meses = somar_meses(valores_por_mes(s, recortes.acumulado, "realizado")).cabecas
    centros = []
    for centro in desembolso_por_centro(s, recortes.acumulado):
        centros.append(CentroDoDesembolso(centro_custo=centro.centro_custo,
                                          valor_mes=do_mes.get(centro.centro_custo, 0),
                                          valor_acumulado=centro.valor,
                                          por_cabeca_mes=dividir(centro.valor, rebanho_dos_meses)))
    return centros


def sem_lancamento(financas: Financeiro) -> bool:
    """Nenhum crédito nem débito no período até o mês de referência."""
    movimentado = 0.0
    for mes in financas.serie_mensal:
        movimentado += abs(mes.receitas) + abs(mes.despesas) + abs(mes.saldo)
    return movimentado == 0


def leitura_financeira(recortes: Recortes, placar: list[LinhaDoPlacar], centros: list[CentroDoDesembolso],
                       sem_lancamento_no_periodo: bool = False) -> list[str]:
    mes = textos.mes_por_extenso(recortes.mes_referencia)
    receitas, desembolso, _, por_cabeca, custeio, _ = placar
    if sem_lancamento_no_periodo:
        return [frase_sem_lancamento(mes, receitas, desembolso)]
    frases = [f"Até {mes}: receitas de {frase_do_valor(receitas)} e desembolso de {frase_do_valor(desembolso)}."]
    if por_cabeca.acumulado.realizado is not None:
        frase = f"O desembolso por cabeça é de {textos.dinheiro(por_cabeca.acumulado.realizado, 2)}/cab/mês"
        if por_cabeca.acumulado.previsto is not None:
            frase += f" (previsto: {textos.dinheiro(por_cabeca.acumulado.previsto, 2)})"
        if custeio.acumulado.realizado is not None:
            frase += f"; o custeio, {textos.dinheiro(custeio.acumulado.realizado, 2)}/cab/mês"
        frases.append(frase + ".")
    total = sum(centro.valor_acumulado for centro in centros)
    if centros and total:
        maior = centros[0]
        frases.append(f"O maior centro de custo é {maior.centro_custo}, com {textos.dinheiro(maior.valor_acumulado)} "
                      f"({textos.percentual(maior.valor_acumulado / total)} do desembolso).")
    return frases


def frase_sem_lancamento(mes: str, receitas: LinhaDoPlacar, desembolso: LinhaDoPlacar) -> str:
    """Sem lançamento, um "R$ 0" pareceria que a fazenda não gastou: a frase diz o que falta e o que era previsto."""
    frase = f"Não há lançamentos financeiros no período (até {mes})"
    if receitas.acumulado.previsto is not None or desembolso.acumulado.previsto is not None:
        frase += (f"; o previsto até aqui era de {textos.dinheiro(receitas.acumulado.previsto or 0)} em receitas e "
                  f"{textos.dinheiro(desembolso.acumulado.previsto or 0)} em desembolso")
    return frase + "."


def frase_do_valor(linha: LinhaDoPlacar) -> str:
    frase = textos.dinheiro(linha.acumulado.realizado or 0)
    if linha.acumulado.variacao_percentual is not None:
        frase += f" ({textos.frente_ao_previsto(linha.acumulado.variacao_percentual)})"
    return frase


def secao_caixa(s: Session, recortes: Recortes) -> SecaoCaixa:
    caixa = previsto_realizado(s, recortes.acumulado)
    frases = [frase_do_resultado(recortes, caixa)]
    vermelhos = []
    for grupo in caixa.grupos:
        for conta in grupo.contas:
            if conta.acumulado.semaforo == "vermelho":
                vermelhos.append(conta)
    vermelhos.sort(key=lambda conta: abs(conta.acumulado.realizado - conta.acumulado.planejado), reverse=True)
    for conta in vermelhos[:3]:
        frases.append(f"Fora do previsto: {conta.nome}, {textos.dinheiro(conta.acumulado.realizado)} contra "
                      f"{textos.dinheiro(conta.acumulado.planejado)} previstos.")
    return SecaoCaixa(previsto_realizado=caixa, leitura=frases)


def frase_do_resultado(recortes: Recortes, caixa: PrevistoRealizado) -> str:
    mes = textos.mes_por_extenso(recortes.mes_referencia)
    resultado = caixa.resultado
    if sem_caixa_realizado(caixa):
        return frase_do_caixa_sem_lancamento(mes, caixa)
    if sem_caixa_previsto(caixa):
        return (f"Resultado do caixa em {mes}: {textos.dinheiro(resultado.mensal.realizado)}; no acumulado, "
                f"{textos.dinheiro(resultado.acumulado.realizado)}. O período não tem fluxo de caixa previsto.")
    return (f"Resultado do caixa em {mes}: {textos.dinheiro(resultado.mensal.realizado)} (previsto "
            f"{textos.dinheiro(resultado.mensal.planejado)}); no acumulado, "
            f"{textos.dinheiro(resultado.acumulado.realizado)} (previsto "
            f"{textos.dinheiro(resultado.acumulado.planejado)}).")


def frase_do_caixa_sem_lancamento(mes: str, caixa: PrevistoRealizado) -> str:
    if sem_caixa_previsto(caixa):
        return f"Não há lançamentos financeiros nem fluxo de caixa previsto no período (até {mes})."
    return (f"Não há lançamentos financeiros no período (até {mes}); o resultado previsto no acumulado é de "
            f"{textos.dinheiro(caixa.resultado.acumulado.planejado)}.")


def sem_caixa_realizado(caixa: PrevistoRealizado) -> bool:
    return all(grupo.total.acumulado.realizado == 0 for grupo in caixa.grupos)


def sem_caixa_previsto(caixa: PrevistoRealizado) -> bool:
    return all(grupo.total.acumulado.planejado == 0 for grupo in caixa.grupos)
