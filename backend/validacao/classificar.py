"""Classifica as diferenças de um cruzamento com o adapter real de planilhas.

    python -m validacao.classificar [cruzamento_AAAAMMDD_adapter.json] [--snapshot AAAA-MM-DD] [--ate AAAA-MM]

O BI de planilhas lê um snapshot do datalake; o adapter lê os .xlsm de hoje. Cada diferença fazenda × mês × medida
cai numa classe:
- `so_bi`: a fazenda não existe mais na pasta (arquivo removido/renomeado depois do snapshot);
- `so_plataforma`: fazenda nova (arquivo criado depois do snapshot);
- `arquivo_alterado`: o .xlsm foi salvo depois do snapshot (o consultor pode ter corrigido meses passados);
- `ja_na_ponte`: a mesma diferença já existia na rodada pela ponte (stg_*), logo já está explicada no relatório;
- `nova`: aparece só com o adapter real, num arquivo que não mudou — é aqui que se investiga.
"""

import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime

from sqlalchemy import create_engine, text

from app.core.config import get_settings
from validacao import bi
from validacao.cruzar import BANCO, CHAVE_FAZENDA, SAIDA, ULTIMO_MES, comparar, nossos


def arquivos_por_chave() -> dict[str, list[dict]]:
    """PROP_FAZ -> arquivos (unidade de origem) que gravaram fatos dessa fazenda."""
    with create_engine(get_settings().url_migracao(BANCO)).connect() as c:
        linhas = c.execute(text(f"""
            WITH chave AS ({CHAVE_FAZENDA}),
            versao AS (
                SELECT fazenda_id, origem_ref FROM fato.inventario
                UNION SELECT fazenda_id, origem_ref FROM fato.mov_animal
                UNION SELECT fazenda_id, origem_ref FROM fato.lancamento_financeiro
                UNION SELECT fazenda_id, origem_ref FROM fato.rebanho_medio_mensal
                UNION SELECT fazenda_id, origem_ref FROM fato.area_mensal
            )
            SELECT DISTINCT k.chave, u.chave AS arquivo, u.metadados->>'mtime' AS mtime
            FROM chave k JOIN versao v USING (fazenda_id)
            JOIN ingest.versao_origem vo ON vo.id = v.origem_ref
            JOIN ingest.unidade_origem u ON u.id = vo.unidade_id
            WHERE k.fonte = 'planilha'
        """)).all()
    out: dict[str, list[dict]] = defaultdict(list)
    for chave, arquivo, mtime in linhas:
        out[chave].append({"arquivo": arquivo, "mtime": mtime})
    return out


def _mtime(valor: str | None) -> datetime | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(valor)
    except ValueError:
        return datetime.fromtimestamp(float(valor))


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--") and not a[:1].isdigit()]
    snapshot = (date.fromisoformat(sys.argv[sys.argv.index("--snapshot") + 1]) if "--snapshot" in sys.argv
                else date(2026, 8, 1))
    arq = SAIDA / (args[0] if args else max(p.name for p in SAIDA.glob("cruzamento_*_adapter.json")))
    adapter = json.loads(arq.read_text(encoding="utf-8"))["planilha"]
    ponte_arq = arq.with_name(arq.name.replace("_adapter", "_ponte"))
    ponte = json.loads(ponte_arq.read_text(encoding="utf-8"))["planilha"] if ponte_arq.exists() else {"diferencas": []}
    na_ponte = {(d["chave"], d["mes"], d["medida"]): d for d in ponte["diferencas"]}
    ate = ULTIMO_MES
    medidas_bi = bi.planilha(ate)
    chaves_bi = {k[0] for k in medidas_bi}
    arquivos = arquivos_por_chave()

    # fazendas comparáveis: nos dois lados e com todo arquivo salvo antes do snapshot
    estaveis = {k for k, arqs in arquivos.items()
                if k in chaves_bi and all((m := _mtime(a["mtime"])) and m.date() < snapshot for a in arqs)}
    nos = nossos()["planilha"]
    r = comparar("planilha", {k: v for k, v in medidas_bi.items() if k[0] in estaveis},
                 {k: v for k, v in nos.items() if k[0] in estaveis})
    print(f"=== fazendas com arquivo inalterado desde {snapshot}: {len(estaveis)} de {len(chaves_bi)} no BI ===")
    print(f"{'medida':<20}{'pares':>7}{'iguais':>8}{'%':>7}{'Σ BI':>20}{'Σ plataforma':>20}")
    for medida, x in r["resumo"].items():
        print(f"{medida:<20}{x['pares']:>7}{x['iguais']:>8}{100 * x['iguais'] / x['pares']:>6.1f}%"
              f"{x['soma_bi']:>20,.2f}{x['soma_nos']:>20,.2f}")
    print()

    classes: Counter = Counter()
    por_medida: dict[str, Counter] = defaultdict(Counter)
    novas: list[dict] = []
    alterados: dict[str, list[dict]] = {}
    vistas = set()
    for d in adapter["diferencas"]:
        chave = (d["chave"], d["mes"], d["medida"])
        vistas.add(chave)
        arqs = arquivos.get(d["chave"], [])
        recente = max((m for a in arqs if (m := _mtime(a["mtime"]))), default=None)
        if not arqs:
            classe = "so_bi"
        elif d["chave"] not in chaves_bi:
            classe = "so_plataforma"
        elif recente and recente.date() >= snapshot:
            classe = "arquivo_alterado"
            alterados[d["chave"]] = arqs
        elif chave in na_ponte and abs(na_ponte[chave]["nos"] - d["nos"]) < 0.01:
            classe = "ja_na_ponte"
        else:
            classe = "nova"
            novas.append({**d, "arquivos": [a["arquivo"] for a in arqs],
                          "ponte_nos": na_ponte.get(chave, {}).get("nos", d["bi"])})
        classes[classe] += 1
        por_medida[d["medida"]][classe] += 1
    resolvidas = [k for k in na_ponte if k not in vistas and k[1] <= ate.isoformat()]
    for k in resolvidas:
        por_medida[k[2]]["resolvida"] += 1

    colunas = ("so_bi", "so_plataforma", "arquivo_alterado", "ja_na_ponte", "nova", "resolvida")
    print(f"cruzamento: {arq.name}  (ponte: {ponte_arq.name if ponte_arq.exists() else '—'}; snapshot {snapshot})")
    print(f"diferenças: {sum(classes.values())}  " + "  ".join(f"{k}={v}" for k, v in classes.most_common())
          + f"  | resolvidas (diferença da ponte que sumiu): {len(resolvidas)}")
    print(f"\n{'medida':<20}" + "".join(f"{c:>17}" for c in colunas))
    for medida, cont in sorted(por_medida.items()):
        print(f"{medida:<20}" + "".join(f"{cont[c]:>17}" for c in colunas))
    print(f"\nfazendas com diferença e arquivo salvo depois de {snapshot}: {len(alterados)}")
    print(f"\n{len(novas)} diferenças novas (arquivo não mudou, não existiam na ponte):")
    por_fazenda: dict[str, list[dict]] = defaultdict(list)
    for n in novas:
        por_fazenda[n["chave"]].append(n)
    for chave, itens in sorted(por_fazenda.items(), key=lambda kv: -len(kv[1])):
        print(f"  {chave} ({len(itens)}): {itens[0]['arquivos']}")
        for n in sorted(itens, key=lambda x: (x["medida"], x["mes"]))[:6]:
            print(f"      {n['mes']} {n['medida']:<18} BI {n['bi']:>14,.2f}  ponte {n['ponte_nos']:>14,.2f}"
                  f"  adapter {n['nos']:>14,.2f}")
    saida = arq.with_name(arq.name.replace(".json", "_classes.json"))
    saida.write_text(json.dumps({"classes": classes, "por_medida": por_medida, "novas": novas,
                                 "resolvidas": resolvidas, "arquivo_alterado": alterados},
                                ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\ndetalhe: {saida}")


if __name__ == "__main__":
    main()
