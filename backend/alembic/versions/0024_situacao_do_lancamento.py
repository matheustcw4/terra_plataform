"""situacao_do_lancamento: a situação do título no realizado (conciliado, pago ou em aberto)

As páginas do financeiro (Previsto × Realizado e Financeiro) e o MENU filtram os lançamentos pela situação do título
(pedido do usuário, 10/11/2026). No Metryx o título ativo está conciliado (pago e conciliado no banco), pago (sem a
conciliação) ou em aberto (sem pagamento); o excluído ("Deletado") não entra. A planilha só traz o que foi pago.
- fato.lancamento_financeiro.situacao: 'conciliado' | 'pago' | 'em_aberto' (o que já estava no banco é 'pago'; a
  carga seguinte de cada fonte grava a situação certa);
- o título em aberto não tem data de pagamento: data_pagamento passa a aceitar NULL, e o mês do caixa
  (`competencia`) passa a ser o do pagamento ou, sem ele, o do vencimento;
- a view fato.v_lancamento_financeiro é recriada para trazer a coluna nova (o `f.*` é fixado na criação).

Revision ID: 0024
Revises: 0023
Create Date: 2026-11-10
"""

from alembic import op

revision = "0024"
down_revision = "0023"
branch_labels = None
depends_on = None

VIEW = """
CREATE VIEW fato.v_lancamento_financeiro WITH (security_invoker = true) AS
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
FROM fato.lancamento_financeiro f
JOIN dim.plano_contas_map m ON m.id = f.plano_contas_map_id
LEFT JOIN dim.centro_custo c ON c.id = m.centro_custo_id
LEFT JOIN dim.subcentro sc ON sc.id = m.subcentro_id
LEFT JOIN dim.centro_custo_fonte r ON r.fonte = f.fonte AND r.centro_custo_id = m.centro_custo_id
"""


def upgrade() -> None:
    op.execute("""
        DROP VIEW fato.v_lancamento_financeiro;
        ALTER TABLE fato.lancamento_financeiro
            ADD COLUMN situacao text NOT NULL DEFAULT 'pago',
            ADD CONSTRAINT ck_lancamento_situacao CHECK (situacao IN ('conciliado', 'pago', 'em_aberto')),
            ALTER COLUMN data_pagamento DROP NOT NULL,
            DROP COLUMN competencia;
        -- o pago tem data de pagamento; o em aberto entra pelo vencimento
        ALTER TABLE fato.lancamento_financeiro
            ADD CONSTRAINT ck_lancamento_data_do_caixa CHECK (
                (situacao = 'em_aberto' AND data_vencimento IS NOT NULL)
                OR (situacao <> 'em_aberto' AND data_pagamento IS NOT NULL)),
            ADD COLUMN competencia date GENERATED ALWAYS AS (
                date_trunc('month', coalesce(data_pagamento, data_vencimento)::timestamp)::date) STORED;
        CREATE INDEX ix_lancamento_consulta ON fato.lancamento_financeiro (fazenda_id, competencia);
        CREATE INDEX ix_lancamento_situacao ON fato.lancamento_financeiro (fazenda_id, situacao);
    """)
    op.execute(VIEW)


def downgrade() -> None:
    op.execute("""
        DROP VIEW fato.v_lancamento_financeiro;
        DELETE FROM fato.lancamento_financeiro WHERE situacao = 'em_aberto';
        DROP INDEX fato.ix_lancamento_situacao;
        ALTER TABLE fato.lancamento_financeiro
            DROP CONSTRAINT ck_lancamento_data_do_caixa,
            DROP COLUMN competencia,
            DROP COLUMN situacao,
            ALTER COLUMN data_pagamento SET NOT NULL;
        ALTER TABLE fato.lancamento_financeiro
            ADD COLUMN competencia date GENERATED ALWAYS AS (
                date_trunc('month', data_pagamento::timestamp)::date) STORED;
        CREATE INDEX ix_lancamento_consulta ON fato.lancamento_financeiro (fazenda_id, competencia);
    """)
    op.execute(VIEW)
