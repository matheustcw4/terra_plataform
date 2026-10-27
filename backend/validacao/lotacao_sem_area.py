"""Onde a lotação fica inflada por meses com rebanho e sem área (Q13, decidido em 16/10/2026: manter como o BI).

    python -m validacao.lotacao_sem_area

A lotação do BI (e da plataforma) é Σ cabeças ÷ Σ área dos meses escolhidos. No mês com rebanho e sem área, as
cabeças entram e a área não, e a lotação sobe. O script lista, por safra, as fazendas e os GRUPOs (todas as fazendas
de um cliente numa origem) em que isso acontece, com a lotação como o BI e como seria contando as cabeças só dos meses
que têm área. Só lê o banco de validação; a anotação está em docs/validacao/2026-10-16_lotacao_meses_sem_area.md.
"""

from datetime import date

from sqlalchemy import Connection, create_engine, text

from app.core.config import get_settings
from validacao.cruzar import BANCO

# rebanho médio (categoria pendente fica fora, como no KPI) e área, casados por fazenda × mês
MESES_DA_FAZENDA = """
WITH rebanho AS (
    SELECT r.fazenda_id, r.competencia, sum(r.qtd_cab) AS cab
    FROM fato.rebanho_medio_mensal r
    LEFT JOIN dim.categoria_map m ON m.id = r.categoria_map_id
    WHERE r.cenario = 'realizado' AND (r.categoria_map_id IS NULL OR m.categoria_bi_id IS NOT NULL)
      AND r.competencia BETWEEN :inicio AND :fim
    GROUP BY 1, 2
),
area AS (
    SELECT fazenda_id, competencia, sum(area_total_ha) AS ha
    FROM fato.area_mensal WHERE cenario = 'realizado' AND competencia BETWEEN :inicio AND :fim GROUP BY 1, 2
),
juntos AS (
    SELECT coalesce(r.fazenda_id, a.fazenda_id) AS fazenda_id, coalesce(r.cab, 0) AS cab, coalesce(a.ha, 0) AS ha
    FROM rebanho r FULL JOIN area a USING (fazenda_id, competencia)
),
origem AS (
    SELECT f.id AS fazenda_id, f.nome, coalesce(f.proprietario, '') AS cliente, min(ff.fonte) AS fonte
    FROM core.fazenda f JOIN core.fazenda_fonte ff ON ff.fazenda_id = f.id
    GROUP BY f.id, f.nome, f.proprietario
)
"""
POR_FAZENDA = MESES_DA_FAZENDA + """
SELECT * FROM (
SELECT o.nome AS quem, o.cliente, o.fonte,
       sum(j.cab) / nullif(sum(j.ha), 0) AS como_bi,
       sum(j.cab) FILTER (WHERE j.ha > 0) / nullif(sum(j.ha), 0) AS corrigida,
       count(*) FILTER (WHERE j.cab > 0 AND j.ha = 0) AS meses_sem_area
FROM juntos j JOIN origem o USING (fazenda_id)
GROUP BY o.fazenda_id, o.nome, o.cliente, o.fonte
HAVING sum(j.ha) > 0 AND count(*) FILTER (WHERE j.cab > 0 AND j.ha = 0) > 0
) afetadas
ORDER BY como_bi / nullif(corrigida, 0) DESC NULLS FIRST, quem
"""
POR_GRUPO = MESES_DA_FAZENDA + """
SELECT * FROM (
SELECT o.cliente AS quem, o.cliente, o.fonte,
       sum(j.cab) / nullif(sum(j.ha), 0) AS como_bi,
       sum(j.cab) FILTER (WHERE j.ha > 0) / nullif(sum(j.ha), 0) AS corrigida,
       count(DISTINCT j.fazenda_id) FILTER (WHERE j.cab > 0 AND j.ha = 0) AS meses_sem_area
FROM juntos j JOIN origem o USING (fazenda_id)
GROUP BY o.cliente, o.fonte
HAVING sum(j.ha) > 0 AND count(*) FILTER (WHERE j.cab > 0 AND j.ha = 0) > 0
) afetados
ORDER BY como_bi / nullif(corrigida, 0) DESC NULLS FIRST, quem
"""
FAZENDAS_COM_AREA = """
SELECT count(DISTINCT fazenda_id) FROM fato.area_mensal
WHERE cenario = 'realizado' AND area_total_ha > 0 AND competencia BETWEEN :inicio AND :fim
"""


def safras_recentes(hoje: date, quantas: int = 3) -> list[tuple[str, date, date]]:
    """(rótulo, primeiro mês, último mês) das últimas safras, a atual só até o mês de hoje."""
    ano_da_atual = hoje.year
    if hoje.month < 7:
        ano_da_atual -= 1
    safras = []
    for ano in range(ano_da_atual - quantas + 1, ano_da_atual + 1):
        fim = date(ano + 1, 6, 1)
        if fim > hoje:
            fim = hoje.replace(day=1)
        safras.append((f"Safra {str(ano)[2:]}/{str(ano + 1)[2:]}", date(ano, 7, 1), fim))
    return safras


def tabela(conexao: Connection, consulta: str, inicio: date, fim: date, coluna_contagem: str) -> list[str]:
    linhas = [f"| Quem | Cliente | Origem | Lotação como o BI | Só meses com área | {coluna_contagem} |",
              "|---|---|---|---|---|---|"]
    for linha in conexao.execute(text(consulta), {"inicio": inicio, "fim": fim}).mappings():
        corrigida = "—"
        if linha["corrigida"] is not None:
            corrigida = f"{float(linha['corrigida']):.2f}"
        linhas.append(f"| {linha['quem']} | {linha['cliente']} | {linha['fonte']} | {float(linha['como_bi']):.2f} | "
                      f"{corrigida} | {linha['meses_sem_area']} |")
    return linhas


def main() -> None:
    engine = create_engine(get_settings().url_migracao(BANCO))
    with engine.connect() as conexao:
        for rotulo, inicio, fim in safras_recentes(date.today()):
            com_area = conexao.scalar(text(FAZENDAS_COM_AREA), {"inicio": inicio, "fim": fim})
            print(f"\n## {rotulo} ({inicio:%m/%Y} a {fim:%m/%Y}): {com_area} fazendas com área\n")
            print("Por fazenda:\n")
            print("\n".join(tabela(conexao, POR_FAZENDA, inicio, fim, "Meses com rebanho e sem área")))
            print("\nNo GRUPO (todas as fazendas do cliente na origem):\n")
            print("\n".join(tabela(conexao, POR_GRUPO, inicio, fim, "Fazendas com mês sem área")))


if __name__ == "__main__":
    main()
