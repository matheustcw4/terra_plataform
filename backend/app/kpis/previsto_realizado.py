"""KPIs da página Previsto × Realizado, a matriz do DRE do BI de planilhas (docs/analises/01 §5.13 e §7.3): por
classificação e por conta (centro de custo), o realizado, o planejado e a variação, no último mês do período e no
acumulado do período, com o semáforo do BI.

Regras:
- a classificação de cada conta vem de `dim.centro_custo` (A - RECEITAS, C - INVESTIMENTOS, D - CUSTEIO, E - OUTROS
  CRÉDITOS, F - OUTROS DÉBITOS, NEUTRO) ou "A CLASSIFICAR" (decisão Q1); "B - DESEMBOLSO" = investimentos + custeio,
  como a linha sintética do BI;
- valor de uma conta = o lado dela: crédito − débito nas classificações de crédito (A, E) e débito − crédito nas de
  débito (C, D, F); assim o estorno abate. Nas contas neutras ou a classificar, que não entram no resultado, a soma
  dos dois lados, como o BI faz em todas (o BI soma débito e crédito da mesma conta como se fossem do mesmo lado);
- acumulado = do início ao fim do período escolhido (P3); "mensal" = o último mês do período;
- resultado = receitas + outros créditos − (investimentos + custeio + outros débitos) (decisão D1, pendente). O BI
  subtrai uma classificação que não existe e deixa os outros débitos e créditos de fora (P1);
- semáforo (a regra do BI, `Icon`): onde mais é melhor (receitas, outros créditos, resultado), verde acima de +3%,
  vermelho abaixo de −3% e amarelo entre os dois; onde menos é melhor (as despesas), verde até 0%, amarelo até +3% e
  vermelho acima. O limiar vem de `dim.parametro`. Neutro e a classificar ficam sem semáforo.
"""

from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.kpis.filtro import Filtro, periodo_do_filtro
from app.kpis.lotes import dividir, numero
from app.schemas.api import Comparacao, GrupoDoPrevisto, LinhaDoPrevisto, PrevistoRealizado

# cenário -> view com a classificação da conta já resolvida (lista fechada: por isso pode entrar no SQL)
VIEW_DO_CENARIO = {"realizado": "fato.v_lancamento_financeiro", "planejado": "fato.v_orcamento_financeiro"}

RECEITAS = "A - RECEITAS"
DESEMBOLSO = "B - DESEMBOLSO"
INVESTIMENTOS = "C - INVESTIMENTOS"
CUSTEIO = "D - CUSTEIO"
OUTROS_CREDITOS = "E - OUTROS CRÉDITOS"
OUTROS_DEBITOS = "F - OUTROS DÉBITOS"
ORDEM = [RECEITAS, DESEMBOLSO, INVESTIMENTOS, CUSTEIO, OUTROS_CREDITOS, OUTROS_DEBITOS, "NEUTRO", "A CLASSIFICAR"]

# classificação -> "credito" (vale crédito − débito; mais é melhor) ou "debito" (débito − crédito; menos é melhor)
LADO = {RECEITAS: "credito", OUTROS_CREDITOS: "credito", INVESTIMENTOS: "debito", CUSTEIO: "debito",
        OUTROS_DEBITOS: "debito", DESEMBOLSO: "debito"}

# TODO(D7): com mais de uma versão de plano por fazenda, o planejado terá de escolher a versão ativa.
POR_CONTA = """
    SELECT v.competencia, v.classificacao, v.centro_custo,
           sum(v.valor) FILTER (WHERE v.natureza = 'C') AS creditos,
           sum(v.valor) FILTER (WHERE v.natureza = 'D') AS debitos
    FROM {view} v
    WHERE v.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND v.competencia = ANY (CAST(:meses AS date[]))
    GROUP BY v.competencia, v.classificacao, v.centro_custo
"""
LIMIAR = "SELECT valor FROM dim.parametro WHERE chave = 'semaforo_limiar'"


@dataclass
class Valores:
    """Realizado e planejado de uma conta (ou de uma soma de contas) no último mês e no período."""
    realizado_no_mes: float = 0.0
    planejado_no_mes: float = 0.0
    realizado: float = 0.0
    planejado: float = 0.0

    def somar(self, outro: "Valores", sinal: int = 1) -> None:
        self.realizado_no_mes += sinal * outro.realizado_no_mes
        self.planejado_no_mes += sinal * outro.planejado_no_mes
        self.realizado += sinal * outro.realizado
        self.planejado += sinal * outro.planejado


def previsto_realizado(s: Session, filtro: Filtro) -> PrevistoRealizado:
    contas = valores_por_conta(s, filtro)
    limiar = float(s.scalar(text(LIMIAR)))
    grupos = []
    for classificacao in ORDEM:
        grupo = montar_grupo(classificacao, contas, limiar)
        if grupo is not None:
            grupos.append(grupo)
    return PrevistoRealizado(periodo=periodo_do_filtro(filtro), ultimo_mes=filtro.fim, grupos=grupos,
                             resultado=linha("RESULTADO", resultado(contas), "credito", limiar))


def valores_por_conta(s: Session, filtro: Filtro) -> dict[tuple[str, str], Valores]:
    """(classificação, conta) -> valores, já do lado da classificação."""
    contas: dict[tuple[str, str], Valores] = {}
    for cenario, view in VIEW_DO_CENARIO.items():
        for registro in s.execute(text(POR_CONTA.format(view=view)), filtro.parametros()).mappings():
            chave = (registro["classificacao"], registro["centro_custo"])
            if chave not in contas:
                contas[chave] = Valores()
            quantia = valor_do_lado(registro["classificacao"], numero(registro, "creditos"),
                                    numero(registro, "debitos"))
            somar_ao_cenario(contas[chave], cenario, quantia, registro["competencia"] == filtro.fim)
    return contas


def valor_do_lado(classificacao: str, creditos: float, debitos: float) -> float:
    lado = LADO.get(classificacao)
    if lado == "credito":
        return creditos - debitos
    if lado == "debito":
        return debitos - creditos
    return creditos + debitos


def somar_ao_cenario(valores: Valores, cenario: str, quantia: float, no_ultimo_mes: bool) -> None:
    if cenario == "realizado":
        valores.realizado += quantia
        if no_ultimo_mes:
            valores.realizado_no_mes += quantia
        return
    valores.planejado += quantia
    if no_ultimo_mes:
        valores.planejado_no_mes += quantia


def total_da_classificacao(contas: dict[tuple[str, str], Valores], classificacao: str) -> Valores:
    total = Valores()
    for (da_conta, _), valores in contas.items():
        if da_conta == classificacao:
            total.somar(valores)
    return total


def montar_grupo(classificacao: str, contas: dict[tuple[str, str], Valores], limiar: float) -> GrupoDoPrevisto | None:
    """O grupo da matriz; vazio (sem conta nenhuma no período) não aparece."""
    lado = LADO.get(classificacao)
    if classificacao == DESEMBOLSO:
        if not tem_conta(contas, INVESTIMENTOS) and not tem_conta(contas, CUSTEIO):
            return None
        total = total_da_classificacao(contas, INVESTIMENTOS)
        total.somar(total_da_classificacao(contas, CUSTEIO))
        return GrupoDoPrevisto(classificacao=classificacao, total=linha(classificacao, total, lado, limiar), contas=[])
    if not tem_conta(contas, classificacao):
        return None
    linhas_das_contas = []
    for da_conta, nome in sorted(contas):
        if da_conta == classificacao:
            linhas_das_contas.append(linha(nome, contas[(da_conta, nome)], lado, limiar))
    total = total_da_classificacao(contas, classificacao)
    return GrupoDoPrevisto(classificacao=classificacao, total=linha(classificacao, total, lado, limiar),
                           contas=linhas_das_contas)


def tem_conta(contas: dict[tuple[str, str], Valores], classificacao: str) -> bool:
    return any(da_conta == classificacao for da_conta, _ in contas)


def resultado(contas: dict[tuple[str, str], Valores]) -> Valores:
    # TODO(D1): resultado = receitas + outros créditos − (investimentos + custeio + outros débitos), a recomendação da
    # proposta; o BI faz receitas − (investimentos + custeio) por engano (P1).
    total = Valores()
    total.somar(total_da_classificacao(contas, RECEITAS))
    total.somar(total_da_classificacao(contas, OUTROS_CREDITOS))
    for despesa in (INVESTIMENTOS, CUSTEIO, OUTROS_DEBITOS):
        total.somar(total_da_classificacao(contas, despesa), sinal=-1)
    return total


def linha(nome: str, valores: Valores, lado: str | None, limiar: float) -> LinhaDoPrevisto:
    return LinhaDoPrevisto(nome=nome,
                           mensal=comparacao(valores.realizado_no_mes, valores.planejado_no_mes, lado, limiar),
                           acumulado=comparacao(valores.realizado, valores.planejado, lado, limiar))


def comparacao(realizado: float, planejado: float, lado: str | None, limiar: float) -> Comparacao:
    variacao = dividir(realizado - planejado, planejado)
    return Comparacao(realizado=realizado, planejado=planejado, variacao=variacao,
                      semaforo=semaforo(variacao, lado, limiar))


def semaforo(variacao: float | None, lado: str | None, limiar: float) -> str | None:
    if variacao is None or lado is None:
        return None
    if lado == "credito":
        if variacao > limiar:
            return "verde"
        if variacao < -limiar:
            return "vermelho"
        return "amarelo"
    if variacao <= 0:
        return "verde"
    if variacao <= limiar:
        return "amarelo"
    return "vermelho"
