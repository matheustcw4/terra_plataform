"""tipo_do_orcamento

O planejado do financeiro passa a ter dois orçamentos, e as telas Previsto × Realizado e Financeiro escolhem qual
comparar com o realizado (pedido do usuário, 29/10/2026):
- fato.orcamento_financeiro.tipo: 'previsao' (o DRE previsto: o `previsao-financeiro` do Metryx e a aba de DRE
  planejado da planilha, o que já existia) ou 'planejamento' (o fluxo de caixa do plano do Metryx, por versão);
- dim.versao_plano.ordem: a ordem das versões (maior = mais recente), para a escolha padrão de versão;
- a view fato.v_orcamento_financeiro é recriada para trazer a coluna nova (o `f.*` da view é fixado na criação).

Revision ID: 0018
Revises: 0017
Create Date: 2026-10-29
"""

from alembic import op

revision = "0018"
down_revision = "0017"
branch_labels = None
depends_on = None

VIEW = """
CREATE VIEW fato.v_orcamento_financeiro WITH (security_invoker = true) AS
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
FROM fato.orcamento_financeiro f
JOIN dim.plano_contas_map m ON m.id = f.plano_contas_map_id
LEFT JOIN dim.centro_custo c ON c.id = m.centro_custo_id
LEFT JOIN dim.subcentro sc ON sc.id = m.subcentro_id
"""


def upgrade() -> None:
    op.execute(
        """
        DROP VIEW fato.v_orcamento_financeiro;
        ALTER TABLE fato.orcamento_financeiro
            ADD COLUMN tipo text NOT NULL DEFAULT 'previsao',
            ADD CONSTRAINT ck_orcamento_financeiro_tipo CHECK (tipo IN ('previsao', 'planejamento'));
        CREATE INDEX ix_orcamento_financeiro_tipo ON fato.orcamento_financeiro (fazenda_id, tipo, versao_plano_id);
        ALTER TABLE dim.versao_plano ADD COLUMN ordem integer;
        COMMENT ON COLUMN dim.versao_plano.ordem IS 'maior = mais recente (escolha padrão de versão nas telas)';
        """
    )
    op.execute(VIEW)


def downgrade() -> None:
    op.execute(
        """
        DROP VIEW fato.v_orcamento_financeiro;
        DELETE FROM fato.orcamento_financeiro WHERE tipo = 'planejamento';
        DROP INDEX fato.ix_orcamento_financeiro_tipo;
        ALTER TABLE fato.orcamento_financeiro DROP COLUMN tipo;
        ALTER TABLE dim.versao_plano DROP COLUMN ordem;
        """
    )
    op.execute(VIEW)
