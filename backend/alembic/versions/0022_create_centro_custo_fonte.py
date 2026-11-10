"""create_centro_custo_fonte: como o relatório de referência de cada fonte conta um centro de custo

Os números de cliente Metryx batem com os relatórios do próprio Metryx (regra do projeto, 20/10/2026), e os de
planilha, com o BI de planilhas. Os dois relatórios contam dois centros de custo de jeitos diferentes (U6, outubro de
2026, conferido contra o relatório financeiro do Metryx; decisão do usuário, 10/11/2026):
- Rebanho Investimento (a compra de animais): o Metryx não põe no desembolso, e o BI de planilhas põe. No Metryx ele
  continua aparecendo como reposição de gado (a "Relação desembolso total" mostra desembolso e reposição);
- Financiamentos débitos: o Metryx conta no custeio (custeio = desembolso − investimentos), e o BI de planilhas não.

As marcas de `dim.centro_custo` valem para as duas fontes; esta tabela guarda só a exceção de uma fonte, e as views dos
lançamentos e do orçamento usam a exceção antes das marcas do subcentro e do centro. Nenhum KPI olha a fonte: a
diferença fica na dimensão, como o de-para de contas (`dim.plano_contas_map`, também por fonte).

Revision ID: 0022
Revises: 0021
Create Date: 2026-11-10
"""

from alembic import op

revision = "0022"
down_revision = "0021"
branch_labels = None
depends_on = None

VIEW = """
CREATE VIEW fato.v_{tabela} WITH (security_invoker = true) AS
SELECT f.*,
       m.centro_custo_id,
       m.subcentro_id,
       m.centro_custo_id IS NULL                                                     AS a_classificar,
       coalesce(c.nome, 'A classificar')                                             AS centro_custo,
       sc.nome                                                                       AS subcentro,
       coalesce(c.classificacao, 'A CLASSIFICAR')                                    AS classificacao,
       coalesce(r.entra_desembolso, sc.entra_desembolso, c.entra_desembolso, false)  AS entra_desembolso,
       coalesce(r.entra_custeio, sc.entra_custeio, c.entra_custeio, false)           AS entra_custeio,
       coalesce(sc.tipo_custeio, c.tipo_custeio)                                     AS tipo_custeio,
       coalesce(r.eh_reposicao, sc.eh_reposicao, c.eh_reposicao, false)              AS eh_reposicao,
       m.nome_centro_origem,
       m.nome_subcentro_origem
FROM fato.{tabela} f
JOIN dim.plano_contas_map m ON m.id = f.plano_contas_map_id
LEFT JOIN dim.centro_custo c ON c.id = m.centro_custo_id
LEFT JOIN dim.subcentro sc ON sc.id = m.subcentro_id
LEFT JOIN dim.centro_custo_fonte r ON r.fonte = f.fonte AND r.centro_custo_id = m.centro_custo_id
"""

VIEW_ANTERIOR = """
CREATE VIEW fato.v_{tabela} WITH (security_invoker = true) AS
SELECT f.*,
       m.centro_custo_id,
       m.subcentro_id,
       m.centro_custo_id IS NULL                                        AS a_classificar,
       coalesce(c.nome, 'A classificar')                                AS centro_custo,
       sc.nome                                                          AS subcentro,
       coalesce(c.classificacao, 'A CLASSIFICAR')                       AS classificacao,
       coalesce(sc.entra_desembolso, c.entra_desembolso, false)         AS entra_desembolso,
       coalesce(sc.entra_custeio, c.entra_custeio, false)               AS entra_custeio,
       coalesce(sc.tipo_custeio, c.tipo_custeio)                        AS tipo_custeio,
       coalesce(sc.eh_reposicao, c.eh_reposicao, false)                 AS eh_reposicao,
       m.nome_centro_origem,
       m.nome_subcentro_origem
FROM fato.{tabela} f
JOIN dim.plano_contas_map m ON m.id = f.plano_contas_map_id
LEFT JOIN dim.centro_custo c ON c.id = m.centro_custo_id
LEFT JOIN dim.subcentro sc ON sc.id = m.subcentro_id
"""

FATOS = ("lancamento_financeiro", "orcamento_financeiro")


def upgrade() -> None:
    op.execute("""
        CREATE TABLE dim.centro_custo_fonte (
            fonte            text     NOT NULL CHECK (fonte IN ('planilha', 'metryx')),
            centro_custo_id  smallint NOT NULL REFERENCES dim.centro_custo(id),
            entra_desembolso boolean,
            entra_custeio    boolean,
            eh_reposicao     boolean,
            motivo           text     NOT NULL,
            PRIMARY KEY (fonte, centro_custo_id)
        );
        COMMENT ON TABLE dim.centro_custo_fonte IS
            'exceção de uma fonte às marcas de dim.centro_custo (NULL = vale a marca do centro)';

        INSERT INTO dim.centro_custo_fonte (fonte, centro_custo_id, entra_desembolso, eh_reposicao, motivo)
        SELECT 'metryx', id, false, true,
               'o relatório financeiro do Metryx não conta a compra de animais no desembolso'
        FROM dim.centro_custo WHERE nome_normalizado = 'REBANHO INVESTIMENTO';

        INSERT INTO dim.centro_custo_fonte (fonte, centro_custo_id, entra_custeio, motivo)
        SELECT 'metryx', id, true,
               'o relatório financeiro do Metryx conta os financiamentos no custeio (custeio = desembolso − investimentos)'
        FROM dim.centro_custo WHERE nome_normalizado = 'FINANCIAMENTOS DEBITOS';
    """)
    for tabela in FATOS:
        op.execute(f"DROP VIEW fato.v_{tabela};")
        op.execute(VIEW.format(tabela=tabela))


def downgrade() -> None:
    for tabela in FATOS:
        op.execute(f"DROP VIEW fato.v_{tabela};")
        op.execute(VIEW_ANTERIOR.format(tabela=tabela))
    op.execute("DROP TABLE dim.centro_custo_fonte;")
