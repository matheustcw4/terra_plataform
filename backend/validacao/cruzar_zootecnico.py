"""Páginas Nascimentos, Mortes e Transferências × medidas do BI de planilhas, em filtros sorteados.

    python -m validacao.cruzar_zootecnico [--sorteios 300] [--semente 7]

Mesmo sorteio do `cruzar_kpis` (1 a 3 fazendas do mesmo cliente, 1 a 12 meses, só fazendas com arquivo inalterado
desde o snapshot). Compara, por recorte e cenário (realizado e planejado):
- Nascimentos (GERAL, MACHO, FÊMEA): cabeças ("Sum(pecuarioNascimento.qtd)", "Sum(fMetasNascimentos.qtd)") e a
  participação do sexo no total ("IN - % Female Birth" / "% Male Birth");
- Mortes (GERAL, BEZERROS, JOVENS, ADULTOS): cabeças ("Dead Quantity", "Dead Quantity - Forecast"), a mortalidade
  sobre o rebanho médio do grupo ("% mORTALITY ( MEAN MONTH)"), a dos bezerros sobre os nascimentos
  ("% Mortality") e as mortes por causa;
- Transferências (entrada e saída × GERAL, MACHO, FÊMEA): cabeças, peso médio e preço da @ ("IN QTD Transfer",
  "IN - AVG Weight Transfer", "IN - AVG Price @ Transfer" e os Forecast).

O lado BI soma as linhas das tabelas do PBIX (o SQL do Power Query como está), com o recorte pela coluna da própria
tabela (sexo, grupo_categoria, operação), como os filtros dos cards, e só datas do calendário do BI. Só entra na
conta o recorte em que algum lado tem número (0 = 0 não prova nada).

Cada diferença é classificada:
- "P3": mortalidade sobre nascimentos. O BI divide pelos nascimentos acumulados desde janeiro (ou desde o início do
  calendário, quando o período pega dois anos civis); a plataforma, pelos nascimentos do período. Conta como P3
  quando o número do BI refeito com os nascimentos do período bate;
- "A17", "A20", "A21", "A22": como no `cruzar_compras_e_vendas`;
- "A23": transferência planejada com QTD fracionária (meta calculada na planilha, ex.: 234,58): o ETL do BI trunca
  para inteiro (234) e a plataforma guarda o número da planilha;
- "A24": QTD com mais de 3 casas decimais na planilha (ex.: meta de morte de 0,55856 cabeça): o canônico guarda 3
  casas por linha e a soma de muitas linhas difere em centésimos;
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
from app.kpis.filtro import Filtro
from app.kpis.mortes import mortes
from app.kpis.nascimentos import nascimentos
from app.kpis.transferencias import transferencias
from app.schemas.api import Mortes
from validacao import bi
from validacao.cruzar import BANCO
from validacao.cruzar_compras_e_vendas import (
    Placar,
    TabelasDoBi,
    causa,
    dividir,
    iguais,
    indicadores_do_bi,
    somas_do_bi,
    totais_do_bi,
    valor,
)
from validacao.cruzar_kpis import ULTIMO_MES, argumento, fazendas_estaveis_por_cliente, meses_do_periodo, sortear_filtro
from validacao.datalake import competencia, consultar, parse_data, sql_do_pbix

CENARIOS = ("realizado", "planejado")
# (página, cenário) -> (tabela do PBIX, coluna do recorte, coluna das cabeças)
CONTAGENS = {
    ("nascimentos", "realizado"): ("pecuarioNascimento", "sexo", "qtd"),
    ("nascimentos", "planejado"): ("fMetasNascimentos", "sexo", "qtd"),
    ("mortes", "realizado"): ("pecuarioMortes", "grupo_categoria", "qtd"),
    ("mortes", "planejado"): ("fMetasMortes", "grupo_categoria", "qtd"),
    ("causas", "realizado"): ("pecuarioMortes", "causa", "qtd"),
    ("rebanho", "realizado"): ("pecuarioRebanhoMedioMensal", "grupo_categoria", "qtd_cab"),
}
TRANSFERENCIAS = TabelasDoBi("fTransferencias", "fMetasTransferencias", "VALOR TOTAL", "total_peso", True, True)
SENTIDOS = {"entrada": "ENTRADA", "saida": "SAIDA"}     # campo da página -> palavra na coluna operação do BI
TIPO_DO_SENTIDO = {"entrada": "TRANSF_ENTRADA", "saida": "TRANSF_SAIDA"}
MEDIDAS_DA_TRANSFERENCIA = ("cabecas", "peso_medio_kg", "preco_arroba")
EXPLICACOES = ("P3", "A17", "A20", "A21", "A22", "A23", "A24", "sem explicação")

QTD_FRACIONARIA = """
    SELECT count(*)
    FROM fato.mov_animal m
    WHERE m.tipo = :tipo AND m.cenario = :cenario AND m.qtd <> trunc(m.qtd)
      AND m.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND m.competencia BETWEEN :inicio AND :fim
"""

Contagens = dict[tuple[str, date, str], dict[str, float]]      # (PROP_FAZ, mês, recorte) -> cabeças e avisos


def contagens_do_bi(tabela: str, coluna_recorte: str, coluna_cabecas: str) -> Contagens:
    contagens: Contagens = defaultdict(lambda: defaultdict(float))
    for linha in consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", tabela)):
        dia = parse_data(linha.get("DATA_2") or linha.get("DATA") or linha.get("data"))
        if dia is None or dia < bi.INICIO_CALENDARIO:          # fora do dCalendar, o card não vê a linha
            continue
        do_grupo = contagens[(linha["prop_faz"], competencia(dia), recorte_da_linha(linha, coluna_recorte))]
        cabecas = valor(linha, coluna_cabecas)
        do_grupo["cabecas"] += cabecas
        if parse_data(linha.get("DATA")) is None:                 # só o conversor das metas leu essa data
            do_grupo["linhas_a20"] += 1
        if abs(cabecas - round(cabecas, 3)) > 1e-9:              # o canônico guarda 3 casas
            do_grupo["linhas_a24"] += 1
    return contagens


def recorte_da_linha(linha: dict, coluna: str) -> str:
    """Sexo, grupo ou causa como o BI agrupa: sem distinguir maiúsculas; vazio vira "NÃO INFORMADO"."""
    texto = (linha[coluna] or "").strip().upper()
    if not texto:
        return "NÃO INFORMADO"
    return texto


def tabelas_do_bi() -> dict:
    do_bi = {}
    for chave, (tabela, coluna_recorte, coluna_cabecas) in CONTAGENS.items():
        do_bi[chave] = contagens_do_bi(tabela, coluna_recorte, coluna_cabecas)
    for sentido, palavra in SENTIDOS.items():
        do_bi[("transferencias", "realizado", sentido)] = somas_do_bi(TRANSFERENCIAS.realizado, TRANSFERENCIAS,
                                                                      palavra)
        do_bi[("transferencias", "planejado", sentido)] = somas_do_bi(TRANSFERENCIAS.metas, TRANSFERENCIAS, palavra)
    return do_bi


@dataclass
class Sorteio:
    """Um filtro sorteado: as fazendas (pela chave do BI e pelo id da plataforma) e o período."""
    s: Session
    placar: Placar
    do_bi: dict
    chaves: list[str]
    filtro: Filtro

    def meses(self) -> list[date]:
        return meses_do_periodo(self.filtro.inicio, self.filtro.fim)

    def total(self, tabela: tuple, recorte: str) -> dict[str, float]:
        """Cabeças (e avisos) do recorte nas fazendas e meses do sorteio; GERAL soma todos os recortes."""
        return totais_do_bi(self.do_bi[tabela], self.chaves, self.meses(), recorte)

    def conferir(self, grupo: tuple, recorte: str, deles: float | None, nosso: float | None,
                 totais: list[dict[str, float]], tipo_no_fato: str = "") -> None:
        """`grupo` = (página, cenário, medida); `tipo_no_fato` só nas transferências (para achar a A23)."""
        if not deles and not nosso:
            return
        igual = iguais(grupo[2], deles, nosso)
        explicacao = ""
        if not igual:
            explicacao = self.explicar(grupo, recorte, totais, tipo_no_fato)
        periodo = f"{self.filtro.inicio:%m/%Y} a {self.filtro.fim:%m/%Y}"
        self.placar.anotar(grupo, igual, explicacao, (recorte, self.chaves, periodo, deles, nosso))

    def explicar(self, grupo: tuple, recorte: str, totais: list[dict[str, float]], tipo_no_fato: str) -> str:
        if tipo_no_fato and self.tem_quantidade_fracionaria(tipo_no_fato, grupo[1]):
            return "A23"
        explicacao = causa(self.s, self.filtro, [grupo[0]], recorte, totais)
        if explicacao != "sem explicação":
            return explicacao
        for total in totais:
            if total["linhas_a24"]:
                return "A24"
        return explicacao

    def tem_quantidade_fracionaria(self, tipo_no_fato: str, cenario: str) -> bool:
        parametros = self.filtro.parametros()
        parametros["tipo"] = tipo_no_fato
        parametros["cenario"] = cenario
        return self.s.scalar(text(QTD_FRACIONARIA), parametros) > 0


# --- Nascimentos ---------------------------------------------------------------------------------------------------

def conferir_nascimentos(sorteio: Sorteio) -> None:
    pagina = nascimentos(sorteio.s, sorteio.filtro)
    todos = sorteio.total(("nascimentos", "realizado"), "GERAL")
    for quadro in pagina.quadro:
        for cenario in CENARIOS:
            deles = sorteio.total(("nascimentos", cenario), quadro.recorte)
            sorteio.conferir(("nascimentos", cenario, "cabecas"), quadro.recorte, deles["cabecas"],
                             getattr(quadro, cenario), [deles])
        do_sexo = sorteio.total(("nascimentos", "realizado"), quadro.recorte)
        sorteio.conferir(("nascimentos", "realizado", "% do total"), quadro.recorte,
                         dividir(do_sexo["cabecas"], todos["cabecas"]), quadro.participacao_no_total, [do_sexo, todos])


# --- Mortes --------------------------------------------------------------------------------------------------------

def conferir_mortes(sorteio: Sorteio) -> None:
    pagina = mortes(sorteio.s, sorteio.filtro)
    for quadro in pagina.quadro:
        for cenario in CENARIOS:
            deles = sorteio.total(("mortes", cenario), quadro.recorte)
            sorteio.conferir(("mortes", cenario, "cabecas"), quadro.recorte, deles["cabecas"],
                             getattr(quadro, cenario), [deles])
        mortos = sorteio.total(("mortes", "realizado"), quadro.recorte)
        sorteio.conferir(("mortes", "realizado", "÷ rebanho médio"), quadro.recorte,
                         dividir(mortos["cabecas"], rebanho_medio_do_bi(sorteio, quadro.recorte)),
                         quadro.sobre_rebanho_medio, [mortos])
    conferir_mortalidade_sobre_nascimentos(sorteio, pagina)
    conferir_causas(sorteio, pagina)


def rebanho_medio_do_bi(sorteio: Sorteio, recorte: str) -> float | None:
    """"Mean Month" com o filtro de grupo do card: Σ cabeças ÷ nº de meses em que o recorte teve rebanho > 0."""
    cabecas_por_mes: dict[date, float] = defaultdict(float)
    meses = sorteio.meses()
    for (chave, mes, grupo), do_grupo in sorteio.do_bi[("rebanho", "realizado")].items():
        if chave not in sorteio.chaves or mes not in meses:
            continue
        if recorte != "GERAL" and grupo != recorte:
            continue
        cabecas_por_mes[mes] += do_grupo["cabecas"]
    meses_com_rebanho = 0
    for cabecas in cabecas_por_mes.values():
        if cabecas > 0:
            meses_com_rebanho += 1
    return dividir(sum(cabecas_por_mes.values()), meses_com_rebanho)


def nascimentos_acumulados_do_bi(sorteio: Sorteio) -> float:
    """"Birth Quantity Accumulated" num card: com um só ano civil no período, de janeiro até o fim; com dois, do
    início do calendário do BI até o fim."""
    if sorteio.filtro.inicio.year == sorteio.filtro.fim.year:
        desde = date(sorteio.filtro.fim.year, 1, 1)
    else:
        desde = bi.INICIO_CALENDARIO
    meses = meses_do_periodo(desde, sorteio.filtro.fim)
    return totais_do_bi(sorteio.do_bi[("nascimentos", "realizado")], sorteio.chaves, meses, "GERAL")["cabecas"]


def conferir_mortalidade_sobre_nascimentos(sorteio: Sorteio, pagina: Mortes) -> None:
    grupo = ("mortes", "realizado", "÷ nascimentos")
    bezerros = quadro_do_recorte(pagina, "BEZERROS")
    mortos = sorteio.total(("mortes", "realizado"), "BEZERROS")["cabecas"]
    deles = dividir(mortos, nascimentos_acumulados_do_bi(sorteio))
    nosso = bezerros.sobre_nascimentos
    if not deles and not nosso:
        return
    igual = iguais(grupo[2], deles, nosso)
    explicacao = ""
    if not igual:
        nascidos_no_periodo = sorteio.total(("nascimentos", "realizado"), "GERAL")["cabecas"]
        explicacao = "sem explicação"
        if iguais(grupo[2], dividir(mortos, nascidos_no_periodo), nosso):
            explicacao = "P3"
    periodo = f"{sorteio.filtro.inicio:%m/%Y} a {sorteio.filtro.fim:%m/%Y}"
    sorteio.placar.anotar(grupo, igual, explicacao, ("BEZERROS", sorteio.chaves, periodo, deles, nosso))


def conferir_causas(sorteio: Sorteio, pagina: Mortes) -> None:
    """As mortes por causa (o gráfico de barras): a lista inteira tem de bater."""
    deles = causas_do_bi(sorteio)
    nosso = {item.causa: item.cabecas for item in pagina.causas}
    if not deles and not nosso:
        return
    igual = mesmas_causas(deles, nosso)
    periodo = f"{sorteio.filtro.inicio:%m/%Y} a {sorteio.filtro.fim:%m/%Y}"
    explicacao = ""
    if not igual:
        explicacao = "sem explicação"
    sorteio.placar.anotar(("mortes", "realizado", "por causa"), igual, explicacao,
                          ("GERAL", sorteio.chaves, periodo, deles, nosso))


def causas_do_bi(sorteio: Sorteio) -> dict[str, float]:
    """Causa -> mortes realizadas no sorteio; o gráfico do BI só mostra causa com mortes > 0."""
    somas: dict[str, float] = defaultdict(float)
    meses = sorteio.meses()
    for (chave, mes, causa_da_morte), do_grupo in sorteio.do_bi[("causas", "realizado")].items():
        if chave in sorteio.chaves and mes in meses:
            somas[causa_da_morte] += do_grupo["cabecas"]
    causas = {}
    for causa_da_morte, cabecas in somas.items():
        if cabecas > 0:
            causas[causa_da_morte] = cabecas
    return causas


def mesmas_causas(deles: dict[str, float], nosso: dict[str, float]) -> bool:
    if deles.keys() != nosso.keys():
        return False
    return all(math.isclose(deles[nome], nosso[nome], abs_tol=0.01) for nome in deles)


def quadro_do_recorte(pagina: Mortes, recorte: str):
    for quadro in pagina.quadro:
        if quadro.recorte == recorte:
            return quadro
    raise ValueError(f"quadro {recorte} ausente")


# --- Transferências ------------------------------------------------------------------------------------------------

def conferir_transferencias(sorteio: Sorteio) -> None:
    pagina = transferencias(sorteio.s, sorteio.filtro)
    for sentido in SENTIDOS:
        for quadro in getattr(pagina, sentido):
            for cenario in CENARIOS:
                total = sorteio.total(("transferencias", cenario, sentido), quadro.recorte)
                deles = indicadores_do_bi(total)
                nosso = getattr(quadro, cenario).model_dump()
                for medida in MEDIDAS_DA_TRANSFERENCIA:
                    sorteio.conferir((f"transf. {sentido}", cenario, medida), quadro.recorte, deles[medida],
                                     nosso[medida], [total], TIPO_DO_SENTIDO[sentido])


def main() -> None:
    sorteios = argumento("--sorteios", 300)
    semente = argumento("--semente", 7)
    gerador = random.Random(semente)
    do_bi = tabelas_do_bi()
    engine = create_engine(get_settings().url_migracao(BANCO))
    por_cliente = fazendas_estaveis_por_cliente(engine, {chave for chave, _ in bi.planilha(ULTIMO_MES)})
    placar = Placar(EXPLICACOES)
    with sessao(engine) as s:
        for _ in range(sorteios):
            fazendas, inicio, fim = sortear_filtro(gerador, por_cliente)
            filtro = Filtro(fazendas=[fazenda_id for _, fazenda_id in fazendas], inicio=inicio, fim=fim)
            sorteio = Sorteio(s, placar, do_bi, [chave for chave, _ in fazendas], filtro)
            conferir_nascimentos(sorteio)
            conferir_mortes(sorteio)
            conferir_transferencias(sorteio)
    print(f"{sorteios} sorteios em {sum(len(v) for v in por_cliente.values())} fazendas estáveis (semente {semente})")
    print("  (cada sorteio conta uma vez por recorte em que algum lado tem número)")
    placar.imprimir()


if __name__ == "__main__":
    main()
