"""Página Previsto × Realizado (a matriz do DRE) × o BI de planilhas, em filtros sorteados.

    python -m validacao.cruzar_previsto [--sorteios 300] [--semente 7]

Mesmo sorteio do `cruzar_kpis`. Para cada classificação (A - RECEITAS, B - DESEMBOLSO, C - INVESTIMENTOS...),
realizado e planejado, no último mês do período e no acumulado, compara a plataforma com a tabela `planejadoXRealizado`
do PBIX (o SQL do Power Query) e o resultado com o total da matriz do BI (receitas − investimentos − custeio).

Para explicar as diferenças, as linhas de `financeiroDre`/`fMetasDre` são somadas de mais dois jeitos:
- "bruto": como o BI soma (valor de débito e crédito juntos, pela classificação do BI), sem o join do
  `planejadoXRealizado`;
- "recalculado": pela regra da plataforma (classificação de `dim.centro_custo`, valor negativo virando a natureza
  oposta, crédito − débito nas classificações de crédito e débito − crédito nas de débito).

Cada diferença é classificada:
- "P1": no resultado, o BI deixa de fora os outros créditos e débitos (subtrai uma classificação que não existe);
  a plataforma soma, como recomenda a D1;
- "P9": a tabela do BI não bate com as próprias linhas do DRE: o join do `planejadoXRealizado` duplica realizado ou
  perde meta (metas de mesmo valor no mês, conta de meta que não existe no realizado);
- "A20": meta com a data digitada errada, na quarentena da plataforma (decisão Q8);
- "P4": a classificação da conta difere: o CASE do SQL do BI não lista a conta (ex.: "Culturas - Despesa") e a
  `dim.centro_custo` a classifica;
- "A25": o BI soma débito e crédito da mesma conta do mesmo lado (um débito numa conta de receita aumenta a receita);
  a plataforma põe cada um do seu lado;
- "A26": linha com operação VERIFICAR: o `planejadoXRealizado` soma (as medidas do Financeiro do BI não); a carga põe
  na quarentena e ela aparece em Pendências;
- "A27": linha sem CENTRO_DE_CUSTO_BI: o `planejadoXRealizado` descarta; a plataforma classifica pela tradução da
  própria planilha ou como "A classificar";
- "nas linhas": diferença do resultado que vem das classificações, já explicadas nelas;
- "sem explicação": o resto.
Quando a plataforma bate com o recalculado, a explicação é a causa que mais pesou nas linhas daquela classificação.
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
from app.kpis.filtro import Filtro
from app.kpis.previsto_realizado import (
    CUSTEIO,
    DESEMBOLSO,
    INVESTIMENTOS,
    LADO,
    OUTROS_CREDITOS,
    OUTROS_DEBITOS,
    RECEITAS,
    previsto_realizado,
)
from app.schemas.api import PrevistoRealizado
from validacao import bi
from validacao.cruzar import BANCO
from validacao.cruzar_compras_e_vendas import Placar, operacao_da_linha, valor
from validacao.cruzar_financeiro import centro_da_linha, natureza_e_valor
from validacao.cruzar_kpis import ULTIMO_MES, argumento, fazendas_estaveis_por_cliente, meses_do_periodo, sortear_filtro
from validacao.datalake import competencia, consultar, parse_data, sql_do_pbix

CENARIOS = ("realizado", "planejado")
JANELAS = ("mensal", "acumulado")
DRE_DO_BI = {"realizado": "financeiroDre", "planejado": "fMetasDre"}
SEM_GRUPO = {"": "NEUTRO", None: "A CLASSIFICAR"}       # o BI deixa vazio ou nulo; a plataforma dá nome
EXPLICACOES = ("P1", "P4", "P9", "A20", "A25", "A26", "A27", "nas linhas", "sem explicação")
DIMENSAO = "SELECT nome, classificacao FROM dim.centro_custo"

Somas = dict[tuple[str, date, str], dict[str, float]]      # (PROP_FAZ, mês, classificação) -> "deles:realizado"...


# --- o lado BI -----------------------------------------------------------------------------------------------------

def grupo_do_bi(classificacao: str | None) -> str:
    if classificacao in SEM_GRUPO:
        return SEM_GRUPO[classificacao]
    return classificacao


def somar_a_tabela_do_bi(somas: Somas) -> dict[str, str]:
    """A tabela da matriz do BI; devolve também a classificação que o BI dá a cada conta (pelo nome)."""
    classificacao_do_bi = {}
    for linha in consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "planejadoXRealizado")):
        grupo = grupo_do_bi(linha["classificacao"])
        do_mes = somas[(linha["prop_faz"], linha["data"], grupo)]
        do_mes["deles:realizado"] += valor(linha, "realizado")
        do_mes["deles:planejado"] += valor(linha, "meta")
        if grupo != DESEMBOLSO:
            classificacao_do_bi[norm_texto(linha["centro_de_custo_bi"])] = grupo
    return classificacao_do_bi


def somar_as_linhas(somas: Somas, cenario: str, classificacao_do_bi: dict[str, str], dimensao: dict[str, str]) -> None:
    for linha in consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", DRE_DO_BI[cenario])):
        dia = parse_data(linha.get("data_pag_corrigida") or linha["data_pag"])
        if dia is None:
            continue
        chave = (linha["prop_faz"], competencia(dia))
        grupo_do_bi = somar_bruto(somas, chave, cenario, linha, classificacao_do_bi)
        if parse_data(linha["data_pag"]) is None:
            somas[(*chave, "*")]["linhas_a20"] += 1      # só o conversor das metas leu a data: quarentena
            continue
        grupo_da_dimensao = somar_recalculado(somas, chave, cenario, linha, dimensao)
        anotar_causa(somas, chave, cenario, linha, grupo_do_bi, grupo_da_dimensao)


def somar_bruto(somas: Somas, chave: tuple, cenario: str, linha: dict,
                classificacao_do_bi: dict[str, str]) -> str | None:
    """Como o BI soma: só conta com centro BI, débito e crédito juntos. Devolve a classificação do BI."""
    if not linha["centro_de_custo_bi"]:
        return None
    grupo = classificacao_do_bi.get(norm_texto(linha["centro_de_custo_bi"]), "A CLASSIFICAR")
    somar_no_grupo(somas, chave, grupo, f"bruto:{cenario}", valor(linha, "valor"))
    return grupo


def somar_recalculado(somas: Somas, chave: tuple, cenario: str, linha: dict, dimensao: dict[str, str]) -> str | None:
    """Pela regra da plataforma (`app/kpis/previsto_realizado.py`). Devolve a classificação da dimensão."""
    operacao = operacao_da_linha(linha)
    if operacao not in ("C", "D"):
        return None                                 # VERIFICAR: na plataforma, quarentena
    natureza, quantia = natureza_e_valor(operacao, valor(linha, "valor"))
    grupo = dimensao.get(norm_texto(centro_da_linha(linha)), "A CLASSIFICAR")
    if natureza_oposta(grupo, natureza):
        quantia = -quantia
    somar_no_grupo(somas, chave, grupo, f"dim:{cenario}", quantia)
    return grupo


def natureza_oposta(grupo: str, natureza: str) -> bool:
    """Débito numa classificação de crédito, ou crédito numa de débito: abate o valor da conta."""
    lado = LADO.get(grupo)
    if lado == "credito":
        return natureza == "D"
    if lado == "debito":
        return natureza == "C"
    return False


def anotar_causa(somas: Somas, chave: tuple, cenario: str, linha: dict, grupo_do_bi: str | None,
                 grupo_da_dimensao: str | None) -> None:
    """Guarda, nas classificações que a linha toca, quanto dela soma diferente no BI e na plataforma, e por quê."""
    causa = causa_da_linha(linha, grupo_do_bi, grupo_da_dimensao)
    if causa is None:
        return
    grupos = {grupo_do_bi, grupo_da_dimensao} - {None}
    for grupo in grupos:
        somar_no_grupo(somas, chave, grupo, f"causa:{cenario}:{causa}", abs(valor(linha, "valor")))


def causa_da_linha(linha: dict, grupo_do_bi: str | None, grupo_da_dimensao: str | None) -> str | None:
    if grupo_do_bi is None:
        return "A27"
    if grupo_da_dimensao is None:
        return "A26"
    if grupo_do_bi != grupo_da_dimensao:
        return "P4"
    natureza, _ = natureza_e_valor(operacao_da_linha(linha), valor(linha, "valor"))
    if natureza_oposta(grupo_da_dimensao, natureza):
        return "A25"
    return None


def somar_no_grupo(somas: Somas, chave: tuple, grupo: str, medida: str, quantia: float) -> None:
    somas[(*chave, grupo)][medida] += quantia
    if grupo in (INVESTIMENTOS, CUSTEIO):
        somas[(*chave, DESEMBOLSO)][medida] += quantia


def tabelas_do_bi(engine) -> Somas:
    dimensao = {}
    with engine.connect() as conexao:
        for nome, classificacao in conexao.execute(text(DIMENSAO)):
            dimensao[norm_texto(nome)] = classificacao
    somas: Somas = defaultdict(lambda: defaultdict(float))
    classificacao_do_bi = somar_a_tabela_do_bi(somas)
    for cenario in CENARIOS:
        somar_as_linhas(somas, cenario, classificacao_do_bi, dimensao)
    return somas


# --- um sorteio ----------------------------------------------------------------------------------------------------

@dataclass
class Sorteio:
    s: Session
    placar: Placar
    somas: Somas
    chaves: list[str]
    filtro: Filtro

    def total(self, grupo: str, janela: str) -> dict[str, float]:
        """"deles:realizado", "bruto:planejado", "dim:realizado"... do grupo, no último mês ou no período."""
        meses = meses_do_periodo(self.filtro.inicio, self.filtro.fim)
        if janela == "mensal":
            meses = [self.filtro.fim]
        total: dict[str, float] = defaultdict(float)
        for (chave, mes, do_grupo), medidas in self.somas.items():
            if chave not in self.chaves or mes not in meses:
                continue
            if do_grupo == grupo or do_grupo == "*":
                for medida, quantia in medidas.items():
                    total[medida] += quantia
        return total

    def tolerancia(self) -> float:
        """Decisão Q4: até R$ 1 por fazenda × mês é arredondamento."""
        return float(len(self.chaves) * len(meses_do_periodo(self.filtro.inicio, self.filtro.fim)))

    def anotar(self, grupo: tuple, igual: bool, explicacao: str, recorte: str, deles, nosso) -> None:
        periodo = f"{self.filtro.inicio:%m/%Y} a {self.filtro.fim:%m/%Y}"
        self.placar.anotar(grupo, igual, explicacao, (recorte, self.chaves, periodo, deles, nosso))


def iguais(a: float, b: float, tolerancia: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=tolerancia)


def explicar(total: dict[str, float], cenario: str, nosso: float, tolerancia: float) -> str:
    if not iguais(total[f"dim:{cenario}"], nosso, tolerancia):
        return "sem explicação"
    if not iguais(total[f"deles:{cenario}"], total[f"bruto:{cenario}"], tolerancia):
        return "P9"
    if total["linhas_a20"]:
        return "A20"
    return causa_que_mais_pesou(total, cenario)


def causa_que_mais_pesou(total: dict[str, float], cenario: str) -> str:
    prefixo = f"causa:{cenario}:"
    maior = 0.0
    explicacao = "sem explicação"
    for medida, quantia in total.items():
        if medida.startswith(prefixo) and quantia > maior:
            maior = quantia
            explicacao = medida.removeprefix(prefixo)
    return explicacao


def valor_da_plataforma(pagina: PrevistoRealizado, grupo: str, janela: str, cenario: str) -> float:
    for do_grupo in pagina.grupos:
        if do_grupo.classificacao == grupo:
            return getattr(getattr(do_grupo.total, janela), cenario)
    return 0.0


def conferir_grupos(sorteio: Sorteio, pagina: PrevistoRealizado) -> None:
    grupos = {RECEITAS, DESEMBOLSO, INVESTIMENTOS, CUSTEIO, OUTROS_CREDITOS, OUTROS_DEBITOS}
    tolerancia = sorteio.tolerancia()
    for grupo in sorted(grupos):
        for janela in JANELAS:
            total = sorteio.total(grupo, janela)
            for cenario in CENARIOS:
                deles = total[f"deles:{cenario}"]
                nosso = valor_da_plataforma(pagina, grupo, janela, cenario)
                if not deles and not nosso:
                    continue
                igual = iguais(deles, nosso, tolerancia)
                explicacao = ""
                if not igual:
                    explicacao = explicar(total, cenario, nosso, tolerancia)
                sorteio.anotar((grupo[:16], cenario, janela), igual, explicacao, grupo, deles, nosso)


def conferir_resultado(sorteio: Sorteio, pagina: PrevistoRealizado) -> None:
    """O total da matriz: o BI faz receitas − investimentos − custeio (P1)."""
    tolerancia = sorteio.tolerancia()
    for janela in JANELAS:
        for cenario in CENARIOS:
            deles = resultado_como_o_bi(sorteio, janela, cenario, "deles")
            nosso = getattr(getattr(pagina.resultado, janela), cenario)
            if not deles and not nosso:
                continue
            igual = iguais(deles, nosso, tolerancia)
            explicacao = ""
            if not igual:
                explicacao = explicar_resultado(sorteio, pagina, janela, cenario, deles)
            sorteio.anotar(("RESULTADO", cenario, janela), igual, explicacao, "RESULTADO", deles, nosso)


def resultado_como_o_bi(sorteio: Sorteio, janela: str, cenario: str, criterio: str) -> float:
    receitas = sorteio.total(RECEITAS, janela)[f"{criterio}:{cenario}"]
    investimentos = sorteio.total(INVESTIMENTOS, janela)[f"{criterio}:{cenario}"]
    custeio = sorteio.total(CUSTEIO, janela)[f"{criterio}:{cenario}"]
    return receitas - investimentos - custeio


def explicar_resultado(sorteio: Sorteio, pagina: PrevistoRealizado, janela: str, cenario: str, deles: float) -> str:
    """P1 quando a conta do BI, feita com os números da plataforma, bate; senão a diferença vem das linhas."""
    nosso_sem_outros = (valor_da_plataforma(pagina, RECEITAS, janela, cenario)
                        - valor_da_plataforma(pagina, INVESTIMENTOS, janela, cenario)
                        - valor_da_plataforma(pagina, CUSTEIO, janela, cenario))
    if iguais(nosso_sem_outros, deles, sorteio.tolerancia()):
        return "P1"
    return "nas linhas"


def main() -> None:
    sorteios = argumento("--sorteios", 300)
    semente = argumento("--semente", 7)
    gerador = random.Random(semente)
    engine = create_engine(get_settings().url_migracao(BANCO))
    somas = tabelas_do_bi(engine)
    por_cliente = fazendas_estaveis_por_cliente(engine, {chave for chave, _ in bi.planilha(ULTIMO_MES)})
    placar = Placar(EXPLICACOES)
    with sessao(engine) as s:
        for _ in range(sorteios):
            fazendas, inicio, fim = sortear_filtro(gerador, por_cliente)
            filtro = Filtro(fazendas=[fazenda_id for _, fazenda_id in fazendas], inicio=inicio, fim=fim)
            sorteio = Sorteio(s, placar, somas, [chave for chave, _ in fazendas], filtro)
            pagina = previsto_realizado(s, filtro)
            conferir_grupos(sorteio, pagina)
            conferir_resultado(sorteio, pagina)
    print(f"{sorteios} sorteios em {sum(len(v) for v in por_cliente.values())} fazendas estáveis (semente {semente})")
    placar.imprimir()


if __name__ == "__main__":
    main()
