"""Página Financeiro × medidas do BI de planilhas, em filtros sorteados.

    python -m validacao.cruzar_financeiro [--sorteios 300] [--semente 7]

Mesmo sorteio do `cruzar_kpis` (1 a 3 fazendas do mesmo cliente, 1 a 12 meses, só fazendas com arquivo inalterado
desde o snapshot). Compara, no realizado e no planejado: receitas ("Revenues"), desembolso ("Outlay"), custeio
("Costing"), desembolso e custeio por cabeça por mês (os velocímetros) e o preço da @ vendida; no realizado, também
despesas ("Expenses Graph"), saldo ("Balance") e o desembolso por centro de custo ("RELAÇÃO DESEMBOLSO TOTAL").

O lado BI soma as linhas de `financeiroDre`/`fMetasDre` (o SQL do PBIX) de dois jeitos:
- como o BI: pela classificação que a própria linha traz da planilha (colunas desembolso, custeio e tipo_custeio);
- pela regra da plataforma: classificação de `dim.centro_custo` pelo nome do centro, valor negativo virando a
  natureza oposta (como a carga faz) e débito − crédito nas contas de desembolso e custeio.
Rebanho médio: `pecuarioRebanhoMedioMensal` e `fMetasRebanhoMedio`. Só entra na conta o que algum lado tem.

Cada diferença é classificada:
- "P4": a plataforma bate com a soma das mesmas linhas pela classificação da dimensão; a diferença é só a
  classificação da conta (a planilha marca a conta de um jeito e `dim.centro_custo` de outro: decisão D3);
- "A20": meta com a data digitada errada ("01/092025"): o SQL das metas do BI corrige, a carga põe a linha na
  quarentena e ela aparece em Pendências (decisão Q8);
- "P2": por cabeça planejado num período sem rebanho realizado (o BI divide a meta pelos meses com rebanho
  REALIZADO e fica vazio; a plataforma usa o rebanho planejado);
- "A3", "A17", "A20": no preço da @, como no `cruzar_compras_e_vendas`;
- "sem explicação": o resto.
"""

import math
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import sessao
from app.etl.adapters.planilha.template import norm_texto
from app.kpis.compras import preco_da_arroba_vendida
from app.kpis.filtro import Filtro
from app.kpis.financeiro import desembolso_por_centro, somar_meses, valores_por_mes
from validacao import bi
from validacao.cruzar import BANCO
from validacao.cruzar_compras_e_vendas import (
    TIPOS,
    Placar,
    causa,
    dividir,
    operacao_da_linha,
    somas_do_bi,
    totais_do_bi,
    valor,
)
from validacao.cruzar_kpis import ULTIMO_MES, argumento, fazendas_estaveis_por_cliente, meses_do_periodo, sortear_filtro
from validacao.cruzar_zootecnico import contagens_do_bi
from validacao.datalake import competencia, consultar, parse_data, sql_do_pbix

CENARIOS = ("realizado", "planejado")
DRE_DO_BI = {"realizado": "financeiroDre", "planejado": "fMetasDre"}
REBANHO_DO_BI = {"realizado": "pecuarioRebanhoMedioMensal", "planejado": "fMetasRebanhoMedio"}
# tipo_custeio do BI sem espaços (as metas vêm sem: "ReceitaPec") -> medida
RECEITAS_DO_BI = {"RECEITAPEC": "receitas", "RECEITASPEC": "receitas", "RECEITAAGR": "receitas",
                  "RECEITASAGR": "receitas", "RECEITAOUTRAS": "outras_receitas"}
MEDIDAS_EM_REAIS = {"realizado": ("receitas", "despesas", "saldo", "desembolso", "custeio"),
                    "planejado": ("receitas", "desembolso", "custeio")}
SEM_CLASSIFICACAO = {"entra_desembolso": False, "entra_custeio": False, "tipo_custeio": None}
EXPLICACOES = ("P2", "P4", "A20", "A3", "A17", "sem explicação")
DIMENSAO = "SELECT nome, entra_desembolso, entra_custeio, tipo_custeio FROM dim.centro_custo"

Somas = dict[tuple[str, date], dict[str, float]]      # (PROP_FAZ, mês) -> "bi:medida" / "dim:medida" -> R$


# --- o lado BI: as linhas do DRE somadas pelos dois critérios ------------------------------------------------------

def dimensao_de_contas(engine) -> dict[str, dict]:
    contas = {}
    with engine.connect() as conexao:
        for linha in conexao.execute(text(DIMENSAO)).mappings():
            contas[norm_texto(linha["nome"])] = dict(linha)
    return contas


def somas_do_dre(tabela: str, dimensao: dict[str, dict]) -> Somas:
    somas: Somas = defaultdict(lambda: defaultdict(float))
    for linha in consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", tabela)):
        dia = parse_data(linha.get("data_pag_corrigida") or linha["data_pag"])
        if dia is None:
            continue
        do_mes = somas[(linha["prop_faz"], competencia(dia))]
        for medida, quantia in medidas_como_o_bi(linha).items():
            do_mes[f"bi:{medida}"] += quantia
        if parse_data(linha["data_pag"]) is None:
            do_mes["linhas_a20"] += 1                 # só o conversor das metas leu a data; a carga põe na quarentena
            continue
        for medida, quantia in medidas_pela_dimensao(linha, dimensao).items():
            do_mes[f"dim:{medida}"] += quantia
    return somas


def medidas_como_o_bi(linha: dict) -> dict[str, float]:
    """O que a linha soma em cada medida pela classificação que ela traz da planilha (as medidas DAX)."""
    quantia = valor(linha, "valor")
    operacao = operacao_da_linha(linha)
    tipo = (linha["tipo_custeio"] or "").replace(" ", "").upper()
    medidas = {}
    if operacao == "C" and tipo in RECEITAS_DO_BI:
        medidas[RECEITAS_DO_BI[tipo]] = quantia
    if operacao == "D":
        medidas["despesas"] = quantia
    if linha["desembolso"] == "DCM":
        medidas["desembolso"] = quantia
    if linha["desembolso"] in ("DCM", "REP.") and operacao == "D":
        medidas[f"centro:{linha['centro_de_custo_bi']}"] = quantia
    if linha["custeio"] == "CCM":
        medidas["custeio"] = quantia
    return medidas


def natureza_e_valor(operacao: str, quantia: float) -> tuple[str, float]:
    """Valor negativo (estorno) vira a natureza oposta com o valor positivo, como a carga grava."""
    if quantia >= 0:
        return operacao, quantia
    if operacao == "C":
        return "D", -quantia
    return "C", -quantia


def medidas_pela_dimensao(linha: dict, dimensao: dict[str, dict]) -> dict[str, float]:
    """O que a linha soma em cada medida pela regra da plataforma (`app/kpis/financeiro.py`)."""
    operacao = operacao_da_linha(linha)
    if operacao not in ("C", "D"):
        return {}                                   # VERIFICAR: na plataforma, quarentena
    natureza, quantia = natureza_e_valor(operacao, valor(linha, "valor"))
    centro = centro_da_linha(linha)
    conta = dimensao.get(norm_texto(centro), SEM_CLASSIFICACAO)
    debito_menos_credito = quantia
    if natureza == "C":
        debito_menos_credito = -quantia
    medidas = {}
    if natureza == "C" and conta["tipo_custeio"] in ("RECEITA_PEC", "RECEITA_AGR"):
        medidas["receitas"] = quantia
    if natureza == "C" and conta["tipo_custeio"] == "RECEITA_OUTRAS":
        medidas["outras_receitas"] = quantia
    if natureza == "D" or conta["entra_desembolso"] or conta["entra_custeio"]:
        medidas["despesas"] = debito_menos_credito
    if conta["entra_desembolso"]:
        medidas["desembolso"] = debito_menos_credito
        medidas[f"centro:{centro}"] = debito_menos_credito
    if conta["entra_custeio"]:
        medidas["custeio"] = debito_menos_credito
    return medidas


def centro_da_linha(linha: dict) -> str:
    """Sem a coluna CENTRO_DE_CUSTO_BI, a carga traduz a conta pelo nome local (o BI deixa a linha sem classificação);
    só as metas trazem o nome local."""
    if linha["centro_de_custo_bi"]:
        return linha["centro_de_custo_bi"]
    return linha.get("centro_de_custo") or ""


def rebanho_do_bi(tabela: str) -> dict[tuple[str, date], float]:
    """(PROP_FAZ, mês) -> cabeças (todos os grupos)."""
    cabecas: dict[tuple[str, date], float] = defaultdict(float)
    for (chave, mes, _), do_grupo in contagens_do_bi(tabela, "grupo_categoria", "qtd_cab").items():
        cabecas[(chave, mes)] += do_grupo["cabecas"]
    return cabecas


def tabelas_do_bi(engine) -> dict:
    dimensao = dimensao_de_contas(engine)
    do_bi = {}
    for cenario in CENARIOS:
        do_bi[("dre", cenario)] = somas_do_dre(DRE_DO_BI[cenario], dimensao)
        do_bi[("rebanho", cenario)] = rebanho_do_bi(REBANHO_DO_BI[cenario])
        for tipo in ("abate", "em_pe"):
            tabela = TIPOS[tipo].realizado
            if cenario == "planejado":
                tabela = TIPOS[tipo].metas
            do_bi[(tipo, cenario)] = somas_do_bi(tabela, TIPOS[tipo])
    return do_bi


# --- um sorteio ----------------------------------------------------------------------------------------------------

@dataclass
class Sorteio:
    s: Session
    placar: Placar
    do_bi: dict
    chaves: list[str]
    filtro: Filtro

    def meses(self) -> list[date]:
        return meses_do_periodo(self.filtro.inicio, self.filtro.fim)

    def periodo(self) -> str:
        return f"{self.filtro.inicio:%m/%Y} a {self.filtro.fim:%m/%Y}"

    def dre(self, cenario: str) -> dict[str, float]:
        """"bi:medida" / "dim:medida" -> R$ nas fazendas e meses do sorteio; o saldo pelos dois critérios."""
        total: dict[str, float] = defaultdict(float)
        meses = self.meses()
        for (chave, mes), do_mes in self.do_bi[("dre", cenario)].items():
            if chave in self.chaves and mes in meses:
                for medida, quantia in do_mes.items():
                    total[medida] += quantia
        for criterio in ("bi", "dim"):
            receitas = total[f"{criterio}:receitas"] + total[f"{criterio}:outras_receitas"]
            total[f"{criterio}:saldo"] = receitas - total[f"{criterio}:despesas"]
        return total

    def cabecas(self, cenario: str) -> tuple[float, int]:
        """Σ do rebanho médio dos meses e quantos meses tiveram rebanho."""
        por_mes: dict[date, float] = defaultdict(float)
        meses = self.meses()
        for (chave, mes), cabecas in self.do_bi[("rebanho", cenario)].items():
            if chave in self.chaves and mes in meses:
                por_mes[mes] += cabecas
        meses_com_rebanho = 0
        for cabecas in por_mes.values():
            if cabecas > 0:
                meses_com_rebanho += 1
        return sum(por_mes.values()), meses_com_rebanho

    def tolerancia_em_reais(self) -> float:
        """Decisão Q4: até R$ 1 por fazenda × mês é arredondamento (o canônico guarda centavos)."""
        return float(len(self.chaves) * len(self.meses()))

    def anotar(self, grupo: tuple, igual: bool, explicacao: str, deles, nosso, recorte: str = "GERAL") -> None:
        self.placar.anotar(grupo, igual, explicacao, (recorte, self.chaves, self.periodo(), deles, nosso))


def iguais(a: float | None, b: float | None, tolerancia: float) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(a, b, rel_tol=1e-4, abs_tol=tolerancia)


def conferir_reais(sorteio: Sorteio, cenario: str, nosso: dict[str, float]) -> None:
    dre = sorteio.dre(cenario)
    tolerancia = sorteio.tolerancia_em_reais()
    for medida in MEDIDAS_EM_REAIS[cenario]:
        deles = dre[f"bi:{medida}"]
        if not deles and not nosso[medida]:
            continue
        igual = iguais(deles, nosso[medida], tolerancia)
        explicacao = ""
        if not igual:
            explicacao = explicar(dre, iguais(dre[f"dim:{medida}"], nosso[medida], tolerancia))
        sorteio.anotar(("financeiro", cenario, medida), igual, explicacao, deles, nosso[medida])


def explicar(dre: dict[str, float], bate_pela_dimensao: bool) -> str:
    """Bate somando as mesmas linhas pela regra da plataforma: a diferença é a data que a carga recusou (A20) ou a
    classificação da conta (P4)."""
    if not bate_pela_dimensao:
        return "sem explicação"
    if dre["linhas_a20"]:
        return "A20"
    return "P4"


def conferir_por_cabeca(sorteio: Sorteio, cenario: str, nosso: dict[str, float | None]) -> None:
    dre = sorteio.dre(cenario)
    cabecas, meses_com_rebanho = sorteio.cabecas(cenario)
    _, meses_com_rebanho_realizado = sorteio.cabecas("realizado")
    for medida in ("desembolso", "custeio"):
        deles = dividir(dre[f"bi:{medida}"], cabecas)
        if cenario == "planejado" and meses_com_rebanho_realizado == 0:
            deles = None                            # o BI divide a meta pelos meses com rebanho realizado
        nosso_da_medida = nosso[medida]
        if not deles and not nosso_da_medida:
            continue
        igual = iguais(deles, nosso_da_medida, 0.01)
        explicacao = ""
        if not igual and cenario == "planejado" and meses_com_rebanho_realizado == 0:
            explicacao = "P2"
        elif not igual:
            explicacao = explicar(dre, iguais(dividir(dre[f"dim:{medida}"], cabecas), nosso_da_medida, 0.01))
        sorteio.anotar(("financeiro", cenario, f"{medida}/cab/mês"), igual, explicacao, deles, nosso_da_medida)


def conferir_preco_da_arroba(sorteio: Sorteio, cenario: str) -> None:
    meses = sorteio.meses()
    abate = totais_do_bi(sorteio.do_bi[("abate", cenario)], sorteio.chaves, meses, "GERAL")
    em_pe = totais_do_bi(sorteio.do_bi[("em_pe", cenario)], sorteio.chaves, meses, "GERAL")
    deles = dividir(abate["valor"] + em_pe["valor"], abate["kg_carcaca"] / 15 + em_pe["kg_vivo"] / 30)
    nosso = preco_da_arroba_vendida(sorteio.s, sorteio.filtro, cenario)
    if deles is None and nosso is None:
        return
    igual = iguais(deles, nosso, 0.01)
    explicacao = ""
    if not igual:
        explicacao = causa(sorteio.s, sorteio.filtro, ["abate", "em_pe"], "GERAL", [abate, em_pe])
    sorteio.anotar(("financeiro", cenario, "preço da @ vendida"), igual, explicacao, deles, nosso)


def conferir_centros(sorteio: Sorteio) -> None:
    """"RELAÇÃO DESEMBOLSO TOTAL": a lista inteira de centros e valores tem de bater."""
    dre = sorteio.dre("realizado")
    deles = centros_do_criterio(dre, "bi")
    recalculado = centros_do_criterio(dre, "dim")
    nosso = {}
    for centro in desembolso_por_centro(sorteio.s, sorteio.filtro):
        nosso[centro.centro_custo] = centro.valor
    if not deles and not nosso:
        return
    tolerancia = sorteio.tolerancia_em_reais()
    igual = mesmos_centros(deles, nosso, tolerancia)
    explicacao = ""
    if not igual:
        explicacao = explicar(dre, mesmos_centros(recalculado, nosso, tolerancia))
    sorteio.anotar(("financeiro", "realizado", "desembolso por centro"), igual, explicacao, deles, nosso)


def centros_do_criterio(dre: dict[str, float], criterio: str) -> dict[str, float]:
    centros = {}
    prefixo = f"{criterio}:centro:"
    for medida, quantia in dre.items():
        if medida.startswith(prefixo) and abs(quantia) >= 0.01:
            centros[medida.removeprefix(prefixo)] = quantia
    return centros


def mesmos_centros(deles: dict[str, float], nosso: dict[str, float], tolerancia: float) -> bool:
    """Compara pelo nome normalizado: a dimensão grava o nome canônico e a planilha pode trazer outra grafia."""
    deles_normalizado = {norm_texto(centro): quantia for centro, quantia in deles.items()}
    nosso_normalizado = {norm_texto(centro): quantia for centro, quantia in nosso.items()}
    if deles_normalizado.keys() != nosso_normalizado.keys():
        return False
    return all(iguais(deles_normalizado[nome], nosso_normalizado[nome], tolerancia) for nome in deles_normalizado)


def valores_da_plataforma(s: Session, filtro: Filtro, cenario: str) -> dict:
    total = somar_meses(valores_por_mes(s, filtro, cenario))
    return {"receitas": total.receitas, "despesas": total.despesas,
            "saldo": total.receitas + total.outras_receitas - total.despesas, "desembolso": total.desembolso,
            "custeio": total.custeio, "desembolso/cab": dividir(total.desembolso, total.cabecas),
            "custeio/cab": dividir(total.custeio, total.cabecas)}


def conferir_sorteio(sorteio: Sorteio) -> None:
    for cenario in CENARIOS:
        nosso = valores_da_plataforma(sorteio.s, sorteio.filtro, cenario)
        conferir_reais(sorteio, cenario, nosso)
        conferir_por_cabeca(sorteio, cenario, {"desembolso": nosso["desembolso/cab"],
                                               "custeio": nosso["custeio/cab"]})
        conferir_preco_da_arroba(sorteio, cenario)
    conferir_centros(sorteio)


def main() -> None:
    sorteios = argumento("--sorteios", 300)
    semente = argumento("--semente", 7)
    gerador = random.Random(semente)
    engine = create_engine(get_settings().url_migracao(BANCO))
    do_bi = tabelas_do_bi(engine)
    por_cliente = fazendas_estaveis_por_cliente(engine, {chave for chave, _ in bi.planilha(ULTIMO_MES)})
    placar = Placar(EXPLICACOES)
    with sessao(engine) as s:
        for _ in range(sorteios):
            fazendas, inicio, fim = sortear_filtro(gerador, por_cliente)
            filtro = Filtro(fazendas=[fazenda_id for _, fazenda_id in fazendas], inicio=inicio, fim=fim)
            conferir_sorteio(Sorteio(s, placar, do_bi, [chave for chave, _ in fazendas], filtro))
    print(f"{sorteios} sorteios em {sum(len(v) for v in por_cliente.values())} fazendas estáveis (semente {semente})")
    placar.imprimir()


if __name__ == "__main__":
    main()
