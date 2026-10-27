"""Cruzamento plataforma × BI atual, por fazenda × mês, com os dados reais dos datalakes.

    python -m validacao.cruzar [--sem-carga] [--ponte-planilha] [--ate AAAA-MM]

Planilhas: adapter REAL lendo os .xlsm de PLANILHAS_DIR (ou a ponte das stg_* com --ponte-planilha).
Metryx: a ponte monta o JSON da API a partir das stg_* e usa o normalizador de produção.

1. cria/migra o banco `terra_validacao` (descartável) e carrega as pontes (stg_* -> motor real -> canônico);
2. reproduz os números do BI (SQL do PBIX + DAX) e os nossos (SQL sobre o canônico);
3. grava o resultado bruto em dados_exemplo/validacao/ (fora do git: tem nomes de clientes) e imprime o resumo.
"""

import json
import random
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal

from alembic import command
from sqlalchemy import create_engine, text

from app.core.config import RAIZ_REPO, get_settings
from app.etl.adapters.planilha.adapter import AdapterPlanilha
from app.etl.pipeline import MotorCarga
from tests.conftest import alembic_cfg, criar_banco
from validacao import bi
from validacao.ponte_metryx import PonteMetryx
from validacao.ponte_planilha import PontePlanilha

BANCO = "terra_validacao"
SAIDA = RAIZ_REPO / "dados_exemplo" / "validacao"
HOJE = date.today()
# último mês comparado: o último completo, ou --ate (o snapshot do datalake de planilhas vai até 07/2026)
ULTIMO_MES = (date.fromisoformat(sys.argv[sys.argv.index("--ate") + 1] + "-01") if "--ate" in sys.argv
              else date(HOJE.year - (HOJE.month == 1), (HOJE.month - 2) % 12 + 1, 1))
TOLERANCIA = Decimal("0.01")

MEDIDAS = ["estoque_final", "compra_cab", "compra_valor", "abate_cab", "abate_faturamento", "abate_kg_vivo",
           "abate_kg_carcaca", "empe_cab", "empe_faturamento", "empe_kg_vivo", "nascimento_cab", "morte_cab",
           "rebanho_medio_cab", "area_total_ha", "fin_credito", "fin_debito"]

# chave do BI: Metryx idCustomer||idFarm; planilha PROP_FAZ = unaccent(proprietário||fazenda sem espaços).
# Com a ponte o id_externo já é o PROP_FAZ; com o adapter real, vem do cadastro da fazenda (fUnidade).
CHAVE_FAZENDA = """
    SELECT v.entidade_id AS fazenda_id, v.fonte,
           CASE WHEN v.fonte = 'metryx' THEN replace(v.id_externo, '|', '')
                WHEN v.id_externo LIKE '%|%' THEN app.unaccent('app.unaccent', replace(concat(f.proprietario, f.nome), ' ', ''))
                ELSE v.id_externo END AS chave
    FROM core.fonte_vinculo v JOIN core.fazenda f ON f.id = v.entidade_id
    WHERE v.entidade = 'fazenda'
"""

NOSSAS = f"""
WITH chave AS ({CHAVE_FAZENDA})
SELECT c.fonte, c.chave, e.competencia, 'estoque_final' AS medida, sum(e.saldo_final) AS valor
FROM fato.estoque_mensal e JOIN chave c USING (fazenda_id) GROUP BY 1, 2, 3
UNION ALL
SELECT c.fonte, c.chave, m.competencia, x.medida, sum(x.valor)
FROM fato.mov_animal m JOIN chave c USING (fazenda_id)
CROSS JOIN LATERAL (VALUES
    (CASE m.tipo WHEN 'COMPRA' THEN 'compra_cab' WHEN 'ABATE' THEN 'abate_cab' WHEN 'VENDA_EM_PE' THEN 'empe_cab'
                 WHEN 'NASCIMENTO' THEN 'nascimento_cab' WHEN 'MORTE' THEN 'morte_cab'
                 -- o BI Metryx conta 'Consumo Abate' dentro de 'Dead Quantity'
                 WHEN 'CONSUMO_DOACAO' THEN CASE WHEN c.fonte = 'metryx' THEN 'morte_cab' END END, m.qtd),
    (CASE m.tipo WHEN 'COMPRA' THEN 'compra_valor' WHEN 'ABATE' THEN 'abate_faturamento'
                 WHEN 'VENDA_EM_PE' THEN 'empe_faturamento' END, m.valor_total),
    (CASE m.tipo WHEN 'ABATE' THEN 'abate_kg_vivo' WHEN 'VENDA_EM_PE' THEN 'empe_kg_vivo' END, m.peso_vivo_total_kg),
    (CASE m.tipo WHEN 'ABATE' THEN 'abate_kg_carcaca' END, m.peso_carcaca_total_kg)
) AS x(medida, valor)
WHERE m.cenario = 'realizado' AND x.medida IS NOT NULL
GROUP BY 1, 2, 3, 4
UNION ALL
SELECT c.fonte, c.chave, r.competencia, 'rebanho_medio_cab', sum(r.qtd_cab)
FROM fato.rebanho_medio_mensal r JOIN chave c USING (fazenda_id) WHERE r.cenario = 'realizado' GROUP BY 1, 2, 3
UNION ALL
SELECT c.fonte, c.chave, a.competencia, 'area_total_ha', sum(a.area_total_ha)
FROM fato.area_mensal a JOIN chave c USING (fazenda_id) WHERE a.cenario = 'realizado' GROUP BY 1, 2, 3
UNION ALL
-- financeiro no recorte do BI: planilha por pagamento; Metryx por VENCIMENTO e fazenda FISCAL (como o BI Metryx).
-- Estornos que a ponte inverteu voltam ao sinal original para comparar com a soma do BI.
SELECT c.fonte, c.chave, l.mes,
       CASE WHEN l.nat = 'C' THEN 'fin_credito' ELSE 'fin_debito' END, sum(l.valor)
FROM (
    SELECT coalesce(CASE WHEN f.fonte = 'metryx' THEN l.fazenda_fiscal_id END, l.fazenda_id) AS fazenda_id,
           CASE WHEN f.fonte = 'metryx' THEN date_trunc('month', l.data_vencimento)::date ELSE l.competencia END AS mes,
           CASE WHEN (l.extra->>'sinal_invertido')::boolean THEN CASE l.natureza WHEN 'C' THEN 'D' ELSE 'C' END
                ELSE l.natureza END AS nat,
           CASE WHEN (l.extra->>'sinal_invertido')::boolean THEN -l.valor ELSE l.valor END AS valor
    FROM fato.lancamento_financeiro l JOIN core.fonte_vinculo f ON f.entidade_id = l.fazenda_id AND f.entidade = 'fazenda'
) l JOIN chave c USING (fazenda_id)
GROUP BY 1, 2, 3, 4
"""


def preparar_e_carregar() -> None:
    criar_banco(BANCO)
    command.upgrade(alembic_cfg(BANCO), "head")
    s = get_settings()
    etl = create_engine(s.url_etl(BANCO))
    motor = MotorCarga(etl, hoje=HOJE, estoque_ate=HOJE)
    planilhas = PontePlanilha() if "--ponte-planilha" in sys.argv else AdapterPlanilha(estabilidade_s=0)
    for ponte in (planilhas, PonteMetryx()):
        r = motor.executar(ponte)
        cont = defaultdict(int)
        for u in r.unidades:
            cont[u.status] += 1
        print(f"carga {ponte.fonte}: {dict(cont)}")
        for u in r.unidades:
            if u.status == "erro":
                print("   ERRO", u.chave, (u.erro or "")[:300])
    superu = create_engine(s.url_migracao(BANCO))
    with superu.begin() as c:   # simula o consultor aceitando as sugestões de categoria Metryx (D6)
        n = c.execute(text("UPDATE dim.categoria_map SET categoria_bi_id = categoria_bi_sugerida_id, "
                           "confirmado_em = now() WHERE fonte LIKE 'metryx%' AND categoria_bi_id IS NULL "
                           "AND categoria_bi_sugerida_id IS NOT NULL")).rowcount
        sem = c.execute(text("SELECT count(*) FROM dim.categoria_map WHERE categoria_bi_id IS NULL")).scalar()
        print(f"categorias Metryx confirmadas pela sugestão: {n}; ainda sem categoria BI: {sem}")
    with etl.begin() as c:
        c.execute(text("SELECT fato.recalcular_estoque_mensal(array_agg(id), :ate) FROM core.fazenda"), {"ate": HOJE})


def nossos() -> dict[str, bi.Medidas]:
    out: dict[str, bi.Medidas] = {"planilha": defaultdict(dict), "metryx": defaultdict(dict)}
    with create_engine(get_settings().url_migracao(BANCO)).connect() as c:
        for fonte, chave, comp, medida, valor in c.execute(text(NOSSAS)):
            out[fonte][(chave, comp)][medida] = Decimal(valor or 0)
    return out


def comparar(nome: str, bi_: bi.Medidas, nos: bi.Medidas) -> dict:
    resumo, difs = {}, []
    chaves = {k for k in set(bi_) | set(nos) if bi.INICIO_CALENDARIO <= k[1] <= ULTIMO_MES}
    for medida in MEDIDAS:
        pares = iguais = 0
        soma_bi = soma_nos = Decimal(0)
        for k in chaves:
            b, n = bi_.get(k, {}).get(medida), nos.get(k, {}).get(medida)
            if b is None and n is None:
                continue
            b, n = b or Decimal(0), n or Decimal(0)
            if b == 0 and n == 0:
                continue
            pares += 1
            soma_bi += b
            soma_nos += n
            if abs(b - n) <= TOLERANCIA:
                iguais += 1
            else:
                difs.append({"fonte": nome, "chave": k[0], "mes": k[1].isoformat(), "medida": medida,
                             "bi": float(b), "nos": float(n), "dif": float(n - b)})
        if pares:
            resumo[medida] = {"pares": pares, "iguais": iguais, "soma_bi": float(soma_bi), "soma_nos": float(soma_nos)}
    return {"resumo": resumo, "diferencas": difs}


def amostra(bi_: bi.Medidas, nos: bi.Medidas, n_fazendas: int, semente: int) -> list[dict]:
    """'Filtros sortidos': fazendas e meses sorteados, todas as medidas lado a lado."""
    rnd = random.Random(semente)
    meses = sorted({k[1] for k in nos if bi.INICIO_CALENDARIO <= k[1] <= ULTIMO_MES})
    fazendas = sorted({k[0] for k in nos})
    linhas = []
    for f in rnd.sample(fazendas, min(n_fazendas, len(fazendas))):
        for m in sorted(rnd.sample(meses, 2)):
            for medida in MEDIDAS:
                b, n = bi_.get((f, m), {}).get(medida), nos.get((f, m), {}).get(medida)
                if b or n:
                    linhas.append({"chave": f, "mes": m.isoformat(), "medida": medida, "bi": float(b or 0),
                                   "nos": float(n or 0)})
    return linhas


def main() -> None:
    if "--sem-carga" not in sys.argv:
        preparar_e_carregar()
    nos = nossos()
    resultado = {}
    for nome, func, semente, n in (("planilha", bi.planilha, 7, 5), ("metryx", bi.metryx, 11, 4)):
        bi_ = func(ULTIMO_MES)
        resultado[nome] = comparar(nome, bi_, nos[nome])
        resultado[nome]["amostra"] = amostra(bi_, nos[nome], n, semente)
        print(f"\n=== {nome}: fazenda × mês de {bi.INICIO_CALENDARIO:%m/%Y} a {ULTIMO_MES:%m/%Y} ===")
        print(f"{'medida':<20}{'pares':>7}{'iguais':>8}{'%':>7}{'Σ BI':>20}{'Σ plataforma':>20}")
        for medida, r in resultado[nome]["resumo"].items():
            print(f"{medida:<20}{r['pares']:>7}{r['iguais']:>8}{100 * r['iguais'] / r['pares']:>6.1f}%"
                  f"{r['soma_bi']:>20,.2f}{r['soma_nos']:>20,.2f}")
    SAIDA.mkdir(parents=True, exist_ok=True)
    modo = "ponte" if "--ponte-planilha" in sys.argv else "adapter"
    arquivo = SAIDA / f"cruzamento_{HOJE:%Y%m%d}_{modo}.json"
    arquivo.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nresultado completo: {arquivo}")


if __name__ == "__main__":
    main()
