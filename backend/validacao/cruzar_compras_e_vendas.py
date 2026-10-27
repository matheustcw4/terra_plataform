"""Páginas Vendas (abate e em pé) e Compras × medidas do BI de planilhas, em filtros sorteados.

    python -m validacao.cruzar_compras_e_vendas [--sorteios 300] [--semente 7]

Mesmo sorteio do `cruzar_kpis` (1 a 3 fazendas do mesmo cliente, 1 a 12 meses, só fazendas com arquivo inalterado
desde o snapshot). Para cada tipo de lote, recorte (GERAL, MACHO, FÊMEA) e cenário (realizado e planejado) compara
cabeças, valor (faturamento ou investimento), preço da @, peso médio e, no abate, o rendimento de carcaça; na venda
em pé e na compra, o preço do kg. Compara também o ágio da página Compras.

O lado BI soma as linhas das tabelas do PBIX (o SQL do Power Query como está: pecuarioVendaAbate/EmPe e
pecuarioCompras, e as metas fMetasAbate/EmPe/Compras) e aplica as medidas DAX: @ do abate e da compra = Σ(peso_arroba
× qtd); @ em pé = Σ pesovivo_total ÷ 30; ágio = (@ de compra − @ vendida) ÷ @ vendida, com a @ vendida =
(faturamento do abate + em pé) ÷ (kg de carcaça do abate ÷ 15 + kg vivo em pé ÷ 30). O recorte por sexo usa a coluna
`sexo` da própria tabela, como o filtro dos cards do BI. Só entra na conta o recorte em que algum lado teve lote
(0 = 0 não prova nada).

Cada diferença é classificada:
- "A3": venda em pé sem cliente na plataforma (o Pentaho descarta a linha; a plataforma mostra, decisão Q3);
- "A17": no BI há linha com total vazio (valor ou peso) e valor por cabeça preenchido (o BI soma 0; a plataforma
  calcula quantidade × valor por cabeça, decisão Q7);
- "A20": meta com data digitada como "DDMM/AAAA" (ex.: 0108/2025): o SQL das metas do BI tira a barra e lê
  01/08/2025; a plataforma põe a linha na quarentena, com aviso, e ela aparece em Pendências (decisão Q8);
- "A21": arroba da compra arredondada na planilha: o BI soma PESO_ARROBA (2 casas) × QTD e a plataforma usa o kg
  vivo ÷ 30 (ex.: 6,13 × 31 = 190,03 @ contra 5.700 ÷ 30 = 190,00 @); diferença abaixo de 1%;
- "A22": linha com o total diferente do valor por cabeça × QTD (ex.: TOTAL_PESO dobrado): o BI acerta a @ pela coluna
  por cabeça, a plataforma usa o total; a carga avisa (TOTAL_INCONSISTENT) e a linha aparece em Pendências;
- "sem explicação": o resto.
"""

import math
import random
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.db.session import sessao
from app.kpis.compras import compras
from app.kpis.filtro import Filtro
from app.kpis.vendas import vendas
from validacao import bi
from validacao.cruzar import BANCO
from validacao.cruzar_kpis import ULTIMO_MES, argumento, fazendas_estaveis_por_cliente, meses_do_periodo, sortear_filtro
from validacao.datalake import competencia, consultar, parse_data, sql_do_pbix


@dataclass(frozen=True)
class TabelasDoBi:
    realizado: str
    metas: str
    coluna_valor: str               # faturamento (venda) ou VALOR TOTAL (compra)
    coluna_kg: str                  # kg vivo total
    arroba_da_planilha: bool        # abate e compra: Σ(peso_arroba × qtd); em pé: Σ kg vivo ÷ 30
    arroba_pelo_peso_vivo: bool     # compra: a plataforma conta a @ pelo kg vivo ÷ 30 (A21/A22 comparam as duas)


TIPOS = {
    "abate": TabelasDoBi("pecuarioVendaAbate", "fMetasAbate", "faturamento", "pesovivo_total", True, False),
    "em_pe": TabelasDoBi("pecuarioVendaEmPe", "fMetasEmPe", "faturamento", "pesovivo_total", False, False),
    "compra": TabelasDoBi("pecuarioCompras", "fMetasCompras", "VALOR TOTAL", "total_peso", True, True),
}
MEDIDAS = {"abate": ["cabecas", "valor", "preco_arroba", "peso_medio_kg", "rendimento_carcaca"],
           "em_pe": ["cabecas", "valor", "preco_arroba", "peso_medio_kg", "preco_kg"],
           "compra": ["cabecas", "valor", "preco_arroba", "peso_medio_kg", "preco_kg"]}
TOLERANCIA = {"rendimento_carcaca": 0.0001, "agio": 0.0001}     # as demais: R$ 0,01, 0,01 cab ou 0,01 kg
EXPLICACOES = ("A3", "A17", "A20", "A21", "A22", "sem explicação")
ARREDONDAMENTO = 0.01               # A21: até 1% de diferença entre a @ da planilha e o kg ÷ 30

Somas = dict[tuple[str, date, str | None], dict[str, float]]

VENDAS_SEM_CLIENTE = """
    SELECT count(*)
    FROM fato.mov_animal m
    LEFT JOIN dim.categoria_map c ON c.id = m.categoria_map_id
    LEFT JOIN dim.categoria_bi b ON b.id = c.categoria_bi_id
    WHERE m.tipo = 'VENDA_EM_PE' AND m.cenario = 'realizado' AND m.contraparte IS NULL
      AND m.fazenda_id = ANY (CAST(:fazendas AS uuid[])) AND m.competencia BETWEEN :inicio AND :fim
      AND (:recorte = 'GERAL' OR b.sexo = :recorte)
"""


def somas_do_bi(tabela: str, tabelas: TabelasDoBi, operacao: str = "") -> Somas:
    """(PROP_FAZ, mês, sexo) -> somas das colunas que as medidas usam. Com `operacao`, só as linhas cuja operação
    contém essa palavra (as transferências de entrada e de saída vêm na mesma tabela)."""
    somas: Somas = defaultdict(lambda: defaultdict(float))
    for linha in consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", tabela)):
        if operacao and operacao not in operacao_da_linha(linha):
            continue
        dia = parse_data(linha.get("DATA_2") or linha["DATA"])      # as metas trazem a data já convertida em DATA_2
        if dia is None:
            continue
        do_grupo = somas[(linha["prop_faz"], competencia(dia), linha["sexo"])]
        qtd = valor(linha, "qtd")
        do_grupo["cabecas"] += qtd
        do_grupo["valor"] += valor(linha, tabelas.coluna_valor)
        do_grupo["kg_vivo"] += valor(linha, tabelas.coluna_kg)
        do_grupo["kg_carcaca"] += valor(linha, "pesomorto_total")
        if tabelas.arroba_da_planilha:
            do_grupo["arrobas"] += valor(linha, "peso_arroba") * qtd
        else:
            do_grupo["arrobas"] += valor(linha, tabelas.coluna_kg) / 30
        if total_vazio(linha, tabelas):
            do_grupo["linhas_a17"] += 1
        if parse_data(linha["DATA"]) is None:                     # só o conversor das metas leu essa data
            do_grupo["linhas_a20"] += 1
        if tabelas.arroba_pelo_peso_vivo:
            do_grupo[diferenca_de_arroba(linha, tabelas, qtd)] += 1
    return somas


def operacao_da_linha(linha: dict) -> str:
    """A coluna da operação vem com a grafia da planilha de origem ("operação", "operaÇÃo")."""
    for coluna, conteudo in linha.items():
        if coluna.lower().startswith("opera"):
            return (conteudo or "").upper()
    return ""


def diferenca_de_arroba(linha: dict, tabelas: TabelasDoBi, qtd: float) -> str:
    """Compara a @ do BI (PESO_ARROBA × QTD) com a da plataforma (kg vivo ÷ 30): igual, A21 ou A22."""
    do_bi = valor(linha, "peso_arroba") * qtd
    da_plataforma = valor(linha, tabelas.coluna_kg) / 30
    diferenca = abs(do_bi - da_plataforma)
    if diferenca < 0.01:
        return "linhas_iguais"
    if diferenca <= ARREDONDAMENTO * max(do_bi, da_plataforma):
        return "linhas_a21"
    return "linhas_a22"


def total_vazio(linha: dict, tabelas: TabelasDoBi) -> bool:
    """A17: a coluna de total está vazia, mas a de valor por cabeça não."""
    valor_vazio = linha.get(tabelas.coluna_valor) is None and linha.get("valor_cab") is not None
    peso_vazio = linha.get(tabelas.coluna_kg) is None and linha.get("peso_vivo") is not None
    return valor_vazio or peso_vazio


def valor(linha: dict, coluna: str) -> float:
    if linha.get(coluna) is None:
        return 0.0
    return float(linha[coluna])


def totais_do_bi(somas: Somas, chaves: list[str], meses: list[date], recorte: str) -> dict[str, float]:
    total: dict[str, float] = defaultdict(float)
    for (chave, mes, sexo), do_grupo in somas.items():
        if chave not in chaves or mes not in meses:
            continue
        if recorte != "GERAL" and sexo != recorte:
            continue
        for coluna, quantia in do_grupo.items():
            total[coluna] += quantia
    return total


def indicadores_do_bi(total: dict[str, float]) -> dict[str, float | None]:
    return {"cabecas": total["cabecas"], "valor": total["valor"],
            "preco_arroba": dividir(total["valor"], total["arrobas"]),
            "peso_medio_kg": dividir(total["kg_vivo"], total["cabecas"]),
            "rendimento_carcaca": dividir(total["kg_carcaca"], total["kg_vivo"]),
            "preco_kg": dividir(total["valor"], total["kg_vivo"])}


def agio_do_bi(compra: dict[str, float], abate: dict[str, float], em_pe: dict[str, float]) -> float | None:
    preco_de_compra = dividir(compra["valor"], compra["arrobas"])
    preco_de_venda = dividir(abate["valor"] + em_pe["valor"], abate["kg_carcaca"] / 15 + em_pe["kg_vivo"] / 30)
    if preco_de_compra is None or not preco_de_venda:
        return None
    return (preco_de_compra - preco_de_venda) / preco_de_venda


def dividir(numerador: float, denominador: float) -> float | None:
    if not denominador:
        return None
    return numerador / denominador


def iguais(medida: str, a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(a, b, rel_tol=1e-6, abs_tol=TOLERANCIA.get(medida, 0.01))


def causa(s, filtro: Filtro, tipos: list[str], recorte: str, totais: list[dict[str, float]]) -> str:
    """A explicação de uma diferença; `tipos` e `totais` são os lotes (do BI) que entram na medida."""
    parametros = filtro.parametros()
    parametros["recorte"] = recorte
    if "em_pe" in tipos and s.scalar(text(VENDAS_SEM_CLIENTE), parametros):
        return "A3"
    if any(total["linhas_a17"] for total in totais):
        return "A17"
    if any(total["linhas_a20"] for total in totais):
        return "A20"
    if any(total["linhas_a22"] for total in totais):
        return "A22"
    if any(total["linhas_a21"] for total in totais):
        return "A21"
    return "sem explicação"


def quadros_da_plataforma(s, filtro: Filtro) -> dict[str, list]:
    return {"abate": vendas(s, filtro, "abate").quadro, "em_pe": vendas(s, filtro, "em_pe").quadro,
            "compra": compras(s, filtro).quadro}


class Placar:
    def __init__(self, explicacoes: tuple[str, ...] = EXPLICACOES):
        self.acertos, self.total, self.causas, self.exemplos = Counter(), Counter(), Counter(), []
        self.explicacoes = explicacoes

    def anotar(self, grupo: tuple, igual: bool, explicacao: str, exemplo: tuple) -> None:
        self.total[grupo] += 1
        if igual:
            self.acertos[grupo] += 1
            return
        self.causas[(grupo, explicacao)] += 1
        if explicacao == "sem explicação" and len(self.exemplos) < 30:
            self.exemplos.append((grupo, *exemplo))

    def imprimir(self) -> None:
        for grupo in sorted(self.total):
            tipo, cenario, medida = grupo
            diferencas = ", ".join(f"{explicacao}: {self.causas[(grupo, explicacao)]}" for explicacao in self.explicacoes)
            print(f"  {tipo:<16} {cenario:<10} {medida:<19} {self.acertos[grupo]:>4}/{self.total[grupo]:<4} "
                  f"{100 * self.acertos[grupo] / self.total[grupo]:5.1f}%   {diferencas}")
        for (tipo, cenario, medida), recorte, chaves, periodo, deles, nosso in self.exemplos:
            print(f"  difere: {tipo} {cenario} {medida} {recorte} {periodo}  BI {deles}  plataforma {nosso}  {chaves}")


def conferir_sorteio(s, placar: Placar, do_bi: dict, chaves: list[str], filtro: Filtro) -> None:
    meses = meses_do_periodo(filtro.inicio, filtro.fim)
    periodo = f"{filtro.inicio:%m/%Y} a {filtro.fim:%m/%Y}"
    for tipo, quadros in quadros_da_plataforma(s, filtro).items():
        for coluna in quadros:
            for cenario in ("realizado", "planejado"):
                nosso = getattr(coluna, cenario).model_dump()
                total = totais_do_bi(do_bi[(tipo, cenario)], chaves, meses, coluna.recorte)
                deles = indicadores_do_bi(total)
                if not nosso["cabecas"] and not deles["cabecas"]:
                    continue
                for medida in MEDIDAS[tipo]:
                    igual = iguais(medida, deles[medida], nosso[medida])
                    explicacao = "" if igual else causa(s, filtro, [tipo], coluna.recorte, [total])
                    placar.anotar((tipo, cenario, medida), igual, explicacao,
                                  (coluna.recorte, chaves, periodo, deles[medida], nosso[medida]))
    totais = [totais_do_bi(do_bi[(tipo, "realizado")], chaves, meses, "GERAL") for tipo in ("compra", "abate", "em_pe")]
    deles = agio_do_bi(*totais)
    nosso = compras(s, filtro).agio
    if deles is None and nosso is None:
        return
    igual = iguais("agio", deles, nosso)
    explicacao = "" if igual else causa(s, filtro, ["compra", "abate", "em_pe"], "GERAL", totais)
    placar.anotar(("compra", "realizado", "agio"), igual, explicacao, ("GERAL", chaves, periodo, deles, nosso))


def main() -> None:
    sorteios = argumento("--sorteios", 300)
    semente = argumento("--semente", 7)
    sorteio = random.Random(semente)
    do_bi = {}
    for tipo, tabelas in TIPOS.items():
        do_bi[(tipo, "realizado")] = somas_do_bi(tabelas.realizado, tabelas)
        do_bi[(tipo, "planejado")] = somas_do_bi(tabelas.metas, tabelas)
    engine = create_engine(get_settings().url_migracao(BANCO))
    por_cliente = fazendas_estaveis_por_cliente(engine, {chave for chave, _ in bi.planilha(ULTIMO_MES)})
    placar = Placar()
    with sessao(engine) as s:
        for _ in range(sorteios):
            fazendas, inicio, fim = sortear_filtro(sorteio, por_cliente)
            filtro = Filtro(fazendas=[fazenda_id for _, fazenda_id in fazendas], inicio=inicio, fim=fim)
            conferir_sorteio(s, placar, do_bi, [chave for chave, _ in fazendas], filtro)
    print(f"{sorteios} sorteios em {sum(len(v) for v in por_cliente.values())} fazendas estáveis (semente {semente})")
    print("  (cada sorteio conta uma vez por recorte GERAL/MACHO/FÊMEA em que houve lote)")
    placar.imprimir()


if __name__ == "__main__":
    main()
