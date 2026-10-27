"""Confere app/etl/adapters/metryx/saldo.py contra o SQL fSaldoGado do PBIX, executado no datalake METRYX.

Uso: python -m validacao.checar_saldo_metryx
"""

from collections import defaultdict
from datetime import date
from decimal import Decimal

from app.etl.adapters.metryx.saldo import RegistroBalanco, fim_do_mes, saldo_fim_de_mes
from validacao.datalake import consultar, parse_data, sql_do_pbix


def saldo_bi() -> dict[tuple[str, date], Decimal]:
    """Σ amountacc por (idpropfaz, fim do mês) — o que a medida 'Saldo Acumulado' soma para um mês."""
    out: dict[tuple[str, date], Decimal] = defaultdict(Decimal)
    for r in consultar("METRYX", sql_do_pbix("metryx", "fSaldoGado")):
        out[(r["idpropfaz"], r["ultimodiames"])] += Decimal(str(r["amountacc"] or 0))
    return out


def saldo_python(ate: date, desempate: str = "primeiro") -> dict[tuple[str, date], Decimal]:
    cats = {c["idcategory"]: c["categorygroup"] for c in consultar(
        "METRYX", 'SELECT idcategory, categorygroup FROM "DATABASE".stg_category')}
    regs = [
        RegistroBalanco(fazenda=b["idcustomer"] + b["idfarm"], retiro=b["retironame"], categoria=b["category"],
                        owner=b["owner"], data=parse_data(b["date"]), quantidade=Decimal(str(b["amount"])),
                        grupo=cats.get(b["uuidcategory"]), ano_safra=b["anosafra"], nascimento=b["birth"],
                        safra=b["harvest"], ordem=i)
        # ordem física (ctid) = ordem em que o Pentaho gravou = ordem do JSON da API
        for i, b in enumerate(consultar("METRYX", 'SELECT * FROM "DATABASE".stg_balanco_pecuario ORDER BY ctid'))
    ]
    out: dict[tuple[str, date], Decimal] = defaultdict(Decimal)
    for (fazenda, _ret, _cat), por_mes in saldo_fim_de_mes(regs, desempate).items():
        meses = sorted(por_mes)
        # forward-fill até o mês de `ate` (o BI gera todos os fins de mês até hoje)
        e, i = meses[0], 0
        while e <= fim_do_mes(ate):
            while i + 1 < len(meses) and meses[i + 1] <= e:
                i += 1
            out[(fazenda, e)] += por_mes[meses[i]]
            e = fim_do_mes(date.fromordinal(e.toordinal() + 1))
    return out


def comparar_desempates() -> None:
    hoje = date.today()
    bi = saldo_bi()
    for desempate in ("maior", "menor", "primeiro", "ultimo"):
        py = saldo_python(hoje, desempate)
        chaves = set(bi) | set(py)
        iguais = sum(1 for k in chaves if abs(bi.get(k, Decimal(0)) - py.get(k, Decimal(0))) <= Decimal("0.001"))
        print(f"desempate '{desempate}': {iguais} de {len(chaves)} fins de mês iguais ao BI")


def main() -> None:
    if "--desempates" in __import__("sys").argv:
        return comparar_desempates()
    hoje = date.today()
    bi, py = saldo_bi(), saldo_python(hoje)
    py_menor, py_maior = saldo_python(hoje, "menor"), saldo_python(hoje, "maior")
    chaves = set(bi) | set(py)
    difs = sorted(((k, bi.get(k, Decimal(0)), py.get(k, Decimal(0))) for k in chaves
                   if abs(bi.get(k, Decimal(0)) - py.get(k, Decimal(0))) > Decimal("0.001")), key=lambda x: x[0])
    print(f"pares (fazenda × fim de mês): {len(chaves)}; iguais: {len(chaves) - len(difs)}; diferentes: {len(difs)}")
    fazendas = defaultdict(int)
    for (f, _e), _b, _p in difs:
        fazendas[f] += 1
    print("fazendas com diferença:", dict(fazendas))
    fora = [(k, b, p) for k, b, p in difs
            if not (py_menor.get(k, Decimal(0)) <= b <= py_maior.get(k, Decimal(0)))]
    print(f"diferenças explicadas por empate de bezerros mamando (BI entre 'menor' e 'maior'): {len(difs) - len(fora)}")
    print(f"diferenças NÃO explicadas: {len(fora)}")
    for k, b, p in fora[:25]:
        print("  ", k, "BI", b, "python", p, "menor", py_menor.get(k), "dif", p - b)


if __name__ == "__main__":
    main()
