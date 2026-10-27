"""KPIs da página Movimentação do Gado × medidas do BI de planilhas, em filtros sorteados.

    python -m validacao.cruzar_kpis [--sorteios 200] [--semente 7]

Usa o banco de validação (já carregado pelo `cruzar`) e só fazendas cujo arquivo não mudou desde o snapshot do BI
(as outras diferem por dado novo, não por cálculo). Para cada sorteio — 1 a 3 fazendas do mesmo cliente e um período
de 1 a 12 meses até 06/2026 — compara os cartões da página do BI:
- estoque final ("Stock Accumulated Final");
- rebanho médio e lotação, em cabeças e em UA ("Mean Month", "UA Median Month": Σ ÷ meses com rebanho > 0;
  "Mean Month Ha", "UA Median Ha": Σ ÷ Σ área);
- nascimentos, mortes, compras e vendas (abate + em pé), realizado e planejado (as tabelas detalhadas e as fMetas*).
O lado BI é montado com as medidas mensais de `validacao/bi.py` (o SQL do PBIX + DAX reproduzidos) e, para as metas,
com as tabelas fMetas* do PBIX.
"""

import random
import sys
from collections import Counter, defaultdict
from datetime import date

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from app.db.session import sessao
from app.kpis.filtro import Filtro
from app.kpis.movimentacao import movimentacao
from validacao import bi
from validacao.classificar import arquivos_por_chave
from validacao.cruzar import BANCO, CHAVE_FAZENDA
from validacao.datalake import competencia, consultar, parse_data, sql_do_pbix

SNAPSHOT = date(2026, 8, 1)
ULTIMO_MES = date(2026, 6, 1)
PRIMEIRO_MES = date(2024, 7, 1)
TOLERANCIA = 0.01
# cartão da página -> medidas mensais de bi.planilha (realizado) e tabelas fMetas* (planejado)
REALIZADO_NO_BI = {"nascimentos": ["nascimento_cab"], "mortes": ["morte_cab"], "compras": ["compra_cab"],
                   "vendas": ["abate_cab", "empe_cab"]}
METAS_NO_BI = {"nascimentos": ["fMetasNascimentos"], "mortes": ["fMetasMortes"], "compras": ["fMetasCompras"],
               "vendas": ["fMetasAbate", "fMetasEmPe"]}


def metas_do_bi() -> dict[tuple[str, date, str], float]:
    """(PROP_FAZ, mês, cartão) -> cabeças planejadas."""
    metas: dict[tuple[str, date, str], float] = defaultdict(float)
    for cartao, tabelas in METAS_NO_BI.items():
        for tabela in tabelas:
            for linha in consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", tabela)):
                dia = parse_data(linha.get("DATA_2") or linha["DATA"])
                if dia is None:
                    continue
                metas[(linha["prop_faz"], competencia(dia), cartao)] += float(linha["qtd"] or 0)
    return metas


def mais_meses(mes: date, quantos: int) -> date:
    total = mes.year * 12 + mes.month - 1 + quantos
    return date(total // 12, total % 12 + 1, 1)


def meses_do_periodo(inicio: date, fim: date) -> list[date]:
    meses = []
    mes = inicio
    while mes <= fim:
        meses.append(mes)
        mes = mais_meses(mes, 1)
    return meses


def kpis_do_bi(medidas: dict, metas: dict, chaves: list[str], inicio: date, fim: date) -> dict[str, float | None]:
    meses = meses_do_periodo(inicio, fim)
    resultado: dict[str, float | None] = {"estoque_final": 0.0}
    for chave in chaves:
        resultado["estoque_final"] += float(medidas.get((chave, fim), {}).get("estoque_final", 0))
    rebanho_por_mes: dict[date, float] = defaultdict(float)
    ua_total = 0.0
    area_total = 0.0
    somas: dict[str, float] = defaultdict(float)
    for mes in meses:
        for chave in chaves:
            do_mes = medidas.get((chave, mes), {})
            rebanho_por_mes[mes] += float(do_mes.get("rebanho_medio_cab", 0))
            ua_total += float(do_mes.get("rebanho_medio_ua", 0))
            area_total += float(do_mes.get("area_total_ha", 0))
            for cartao, colunas in REALIZADO_NO_BI.items():
                somas[cartao] += sum(float(do_mes.get(coluna, 0)) for coluna in colunas)
                somas[f"{cartao}_planejado"] += metas.get((chave, mes, cartao), 0.0)
    meses_com_rebanho = sum(1 for cabecas in rebanho_por_mes.values() if cabecas > 0)
    total_rebanho = sum(rebanho_por_mes.values())
    resultado["rebanho_medio_cab"] = total_rebanho / meses_com_rebanho if meses_com_rebanho else None
    resultado["lotacao_cab_ha"] = total_rebanho / area_total if meses_com_rebanho and area_total else None
    resultado["rebanho_medio_ua"] = ua_total / meses_com_rebanho if meses_com_rebanho and ua_total else None
    resultado["lotacao_ua_ha"] = ua_total / area_total if meses_com_rebanho and ua_total and area_total else None
    resultado.update(somas)
    return resultado


def kpis_da_plataforma(s, fazendas: list, inicio: date, fim: date) -> dict[str, float | None]:
    pagina = movimentacao(s, Filtro(fazendas=fazendas, inicio=inicio, fim=fim))
    resultado: dict[str, float | None] = {
        "estoque_final": pagina.estoque_final, "rebanho_medio_cab": pagina.rebanho_medio_cab,
        "lotacao_cab_ha": pagina.lotacao_cab_ha, "rebanho_medio_ua": pagina.rebanho_medio_ua,
        "lotacao_ua_ha": pagina.lotacao_ua_ha}
    for cartao in REALIZADO_NO_BI:
        com_meta = getattr(pagina, cartao)
        resultado[cartao] = com_meta.realizado
        resultado[f"{cartao}_planejado"] = com_meta.planejado
    return resultado


def iguais(a: float | None, b: float | None) -> bool:
    if a is None or b is None:
        return a is None and b is None
    return abs(a - b) <= TOLERANCIA


def fazendas_estaveis_por_cliente(engine, chaves_do_bi: set[str]) -> dict:
    """cliente_id -> [(chave do BI, fazenda_id)] das fazendas cujo arquivo não mudou desde o snapshot do BI."""
    with engine.connect() as conexao:
        linhas = conexao.execute(text(f"SELECT k.chave, k.fazenda_id, f.cliente_id FROM ({CHAVE_FAZENDA}) k "
                                      "JOIN core.fazenda f ON f.id = k.fazenda_id WHERE k.fonte = 'planilha' "
                                      "ORDER BY k.chave")).all()   # ordem fixa: o mesmo sorteio a cada execução
    arquivos = arquivos_por_chave()
    por_cliente: dict = defaultdict(list)
    for chave, fazenda_id, cliente_id in linhas:
        datas = [float(a["mtime"]) for a in arquivos.get(chave, []) if a["mtime"]]
        estavel = datas and all(date.fromtimestamp(d) < SNAPSHOT for d in datas)
        if estavel and chave in chaves_do_bi:
            por_cliente[cliente_id].append((chave, fazenda_id))
    return por_cliente


def sortear_filtro(sorteio: random.Random, por_cliente: dict) -> tuple[list, date, date]:
    """1 a 3 fazendas do mesmo cliente e um período de 1 a 12 meses entre PRIMEIRO_MES e ULTIMO_MES."""
    cliente = sorteio.choice(sorted(por_cliente, key=str))
    quantas = min(len(por_cliente[cliente]), sorteio.randint(1, 3))
    fazendas = sorteio.sample(por_cliente[cliente], k=quantas)
    duracao = sorteio.randint(1, 12)
    inicio = mais_meses(PRIMEIRO_MES, sorteio.randint(0, 24 - duracao))
    fim = mais_meses(inicio, duracao - 1)
    return fazendas, inicio, fim


def argumento(nome: str, padrao: int) -> int:
    if nome in sys.argv:
        return int(sys.argv[sys.argv.index(nome) + 1])
    return padrao


def main() -> None:
    sorteios = argumento("--sorteios", 200)
    semente = argumento("--semente", 7)
    sorteio = random.Random(semente)
    medidas = bi.planilha(ULTIMO_MES)
    metas = metas_do_bi()
    engine = create_engine(get_settings().url_migracao(BANCO))
    por_cliente = fazendas_estaveis_por_cliente(engine, {chave for chave, _ in medidas})

    acertos, total, exemplos = Counter(), Counter(), []
    with sessao(engine) as s:
        for _ in range(sorteios):
            fazendas, inicio, fim = sortear_filtro(sorteio, por_cliente)
            do_bi = kpis_do_bi(medidas, metas, [chave for chave, _ in fazendas], inicio, fim)
            da_plataforma = kpis_da_plataforma(s, [fazenda_id for _, fazenda_id in fazendas], inicio, fim)
            for medida, valor_bi in do_bi.items():
                total[medida] += 1
                if iguais(valor_bi, da_plataforma[medida]):
                    acertos[medida] += 1
                elif len(exemplos) < 25:
                    exemplos.append((medida, [c for c, _ in fazendas], f"{inicio:%m/%Y} a {fim:%m/%Y}", valor_bi,
                                     da_plataforma[medida]))
    print(f"{sorteios} sorteios em {sum(len(v) for v in por_cliente.values())} fazendas estáveis (semente {semente})")
    for medida in total:
        print(f"  {medida:<20} {acertos[medida]:>4}/{total[medida]:<4} {100 * acertos[medida] / total[medida]:5.1f}%")
    for medida, chaves, periodo, valor_bi, valor_nosso in exemplos:
        print(f"  difere: {medida:<18} {periodo}  BI {valor_bi}  plataforma {valor_nosso}  {chaves}")


if __name__ == "__main__":
    main()
