"""Gera as tabelas Markdown do cruzamento a partir do JSON de validacao.cruzar (sem nomes de pessoas).

    python -m validacao.relatorio dados_exemplo/validacao/cruzamento_AAAAMMDD.json
"""

import json
import sys
from collections import defaultdict
from pathlib import Path

from validacao.datalake import consultar

ROTULO_MEDIDA = {
    "estoque_final": "Estoque final (cab)", "compra_cab": "Compras (cab)", "compra_valor": "Compras (R$)",
    "abate_cab": "Abate (cab)", "abate_faturamento": "Abate (R$)", "abate_kg_vivo": "Abate (kg vivo)",
    "abate_kg_carcaca": "Abate (kg carcaça)", "empe_cab": "Em pé (cab)", "empe_faturamento": "Em pé (R$)",
    "empe_kg_vivo": "Em pé (kg vivo)", "nascimento_cab": "Nascimentos (cab)", "morte_cab": "Mortes (cab)",
    "rebanho_medio_cab": "Rebanho médio (cab)", "area_total_ha": "Área total (ha)",
    "fin_credito": "Financeiro créditos (R$)", "fin_debito": "Financeiro débitos (R$)",
}


def rotulos() -> dict[str, str]:
    """Chave do BI -> 'código · FAZENDA' (planilha) ou 'FAZENDA' (Metryx), sem o nome do proprietário."""
    out = {}
    for r in consultar("DATALAKE_PLAN", '''SELECT unaccent(replace(concat("proprietÁrio", fazenda), ' ', '')) pf,
                                           "CÓDIGO PROJETO" cod, fazenda FROM "DATABASE".stg_unidades'''):
        cod = str(r["cod"] or "?").removesuffix(",0")
        out[r["pf"]] = f"{cod} · {r['fazenda']}"
    for r in consultar("METRYX", 'SELECT idcustomer, idfarm, farmname FROM "DATABASE".stg_farm'):
        out[r["idcustomer"] + r["idfarm"]] = f"{r['farmname']} (Metryx {r['idcustomer'][:4]})"
    return out


def fmt(v: float) -> str:
    return f"{v:,.0f}".replace(",", ".") if abs(v) >= 100 or v == int(v) else f"{v:,.2f}".replace(",", "X").replace(
        ".", ",").replace("X", ".")


def main() -> None:
    res = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    nomes = rotulos()
    for fonte, r in res.items():
        print(f"\n### {fonte}\n")
        print("| Medida | Pares fazenda×mês | Iguais | % | Σ BI | Σ plataforma |")
        print("|---|---:|---:|---:|---:|---:|")
        for m, x in r["resumo"].items():
            print(f"| {ROTULO_MEDIDA[m]} | {x['pares']} | {x['iguais']} | {100 * x['iguais'] / x['pares']:.1f}% | "
                  f"{fmt(x['soma_bi'])} | {fmt(x['soma_nos'])} |")
        por_medida = defaultdict(list)
        for d in r["diferencas"]:
            por_medida[d["medida"]].append(d)
        print("\nMaiores diferenças por medida:\n")
        for m, ds in por_medida.items():
            fazendas = len({d["chave"] for d in ds})
            print(f"- **{ROTULO_MEDIDA[m]}**: {len(ds)} pares em {fazendas} fazenda(s)")
            for d in sorted(ds, key=lambda d: -abs(d["dif"]))[:4]:
                print(f"  - {nomes.get(d['chave'], d['chave'][:20])} {d['mes'][:7]}: BI {fmt(d['bi'])} × "
                      f"plataforma {fmt(d['nos'])} (dif {fmt(d['dif'])})")
        print("\nAmostra sorteada:\n")
        print("| Fazenda | Mês | Medida | BI | Plataforma | Dif |")
        print("|---|---|---|---:|---:|---:|")
        for a in r["amostra"]:
            dif = a["nos"] - a["bi"]
            print(f"| {nomes.get(a['chave'], a['chave'][:20])} | {a['mes'][:7]} | {ROTULO_MEDIDA[a['medida']]} | "
                  f"{fmt(a['bi'])} | {fmt(a['nos'])} | {'' if abs(dif) < 0.01 else fmt(dif)} |")


if __name__ == "__main__":
    main()
