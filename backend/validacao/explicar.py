"""Detalha uma divergência do cruzamento: abre fluxos e checkpoints mês a mês, BI × plataforma.

    python -m validacao.explicar planilha <PROP_FAZ> <AAAA-MM>
    python -m validacao.explicar metryx <idcustomer><idfarm> <AAAA-MM>
"""

import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from validacao import bi
from validacao.cruzar import CHAVE_FAZENDA
from validacao.datalake import competencia, consultar, parse_data, sql_do_pbix

OP_TIPO = {"COMPRA": "COMPRA", "NASCIMENTO": "NASCIMENTO", "Transf. Entrada": "TRANSF_ENTRADA", "ABATE": "ABATE",
           "EMPÉ": "VENDA_EM_PE", "MORTE": "MORTE", "Consumo/Doação": "CONSUMO_DOACAO",
           "Transf. Saida": "TRANSF_SAIDA", "DESMAME": "DESMAME", "Mud. de Categoria": "MUDANCA_CATEGORIA",
           "Saldo Anterior": "SALDO"}


def fluxos_bi_planilha(pf: str) -> dict[tuple[date, str], Decimal]:
    out: dict[tuple[date, str], Decimal] = defaultdict(Decimal)
    for r in consultar("DATALAKE_PLAN", sql_do_pbix("ciclo", "fMovGado")):
        if r["prop_faz"] != pf:
            continue
        dt, qtd = parse_data(r["DATA"]), Decimal(str(r["qtd"] or 0))
        qtd_c = qtd if qtd < 0 else (-qtd if r["operaÇÃo"] in bi.SAIDAS else qtd)
        out[(competencia(dt), OP_TIPO.get(r["operaÇÃo"], r["operaÇÃo"]))] += qtd_c
    return out


def fluxos_nossos(chave_externa: str, fonte: str) -> dict[tuple[date, str], Decimal]:
    out: dict[tuple[date, str], Decimal] = defaultdict(Decimal)
    eng = create_engine(get_settings().url_migracao("terra_validacao"))
    with eng.connect() as c:
        fid = c.execute(text(f"SELECT fazenda_id FROM ({CHAVE_FAZENDA}) x WHERE fonte = :f AND chave = :k"),
                        {"f": fonte, "k": chave_externa}).scalar()
        for comp, tipo, valor in c.execute(text("""
            SELECT competencia, tipo, sum(CASE WHEN tipo IN ('COMPRA','NASCIMENTO','TRANSF_ENTRADA') THEN qtd
                                               WHEN tipo IN ('DESMAME','MUDANCA_CATEGORIA') THEN 0 ELSE -qtd END)
            FROM fato.mov_animal WHERE fazenda_id = :f AND cenario = 'realizado' GROUP BY 1, 2
            UNION ALL
            SELECT date_trunc('month', data)::date, 'CHECKPOINT', sum(qtd) FROM fato.inventario WHERE fazenda_id = :f
            GROUP BY 1
            UNION ALL
            SELECT competencia, 'AJUSTE', sum(ajuste) FROM fato.estoque_mensal WHERE fazenda_id = :f GROUP BY 1
            UNION ALL
            SELECT competencia, 'ESTOQUE', sum(saldo_final) FROM fato.estoque_mensal WHERE fazenda_id = :f GROUP BY 1
        """), {"f": fid}):
            out[(comp, tipo)] += Decimal(valor or 0)
        quarentena = c.execute(text("SELECT entidade, codigo, count(*) FROM ingest.linha_quarentena "
                                    "WHERE fazenda_id = :f GROUP BY 1, 2"), {"f": fid}).all()
        print("quarentena:", quarentena)
    return out


def main() -> None:
    fonte, chave, mes = sys.argv[1], sys.argv[2], date.fromisoformat(sys.argv[3] + "-01")
    nos = fluxos_nossos(chave, fonte)
    if fonte == "planilha":
        b = fluxos_bi_planilha(chave)
        meses = sorted({m for m, _ in b} | {m for m, _ in nos if m <= mes})
        tipos = sorted({t for _, t in b} | {t for _, t in nos})
        print(f"{'mês':<9}" + "".join(f"{t[:11]:>13}" for t in tipos))
        for m in meses:
            if m > mes:
                continue
            print(f"BI  {m:%m/%y}" + "".join(f"{b.get((m, t), 0):>13,.0f}" for t in tipos))
            print(f"nós {m:%m/%y}" + "".join(f"{nos.get((m, t), 0):>13,.0f}" for t in tipos))
    else:
        for (m, t), v in sorted(nos.items()):
            if m <= mes:
                print(m, t, v)


if __name__ == "__main__":
    main()
