"""planejado_so_do_planejamento: o planejado do financeiro é só o planejamento

Pedido do usuário (27/11/2026): "planejamento é planejamento e vem dos endpoints"; a previsão financeira do Metryx
(`previsao-financeiro`, a previsão de contas a pagar e a receber) nunca é planejado. A carga deixa de gravá-la
(adapters/metryx/planejamento.py), e esta migração:
- apaga a previsão do Metryx que já estava no orçamento e a versão própria dela ("previsão financeira, sem versão");
- muda o rótulo do DRE planejado da planilha para 'planejamento' (é o planejamento dela; os valores não mudam);
- o tipo novo padrão do orçamento passa a ser 'planejamento'.
O bruto continua guardado: a previsão sai só do planejado, e o downgrade não a recria (uma carga antiga do bruto,
pelo `reprocessar`, também não, porque o adapter novo não a lê).

Revision ID: 0032
Revises: 0031
Create Date: 2026-11-27
"""

from alembic import op

revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        DELETE FROM fato.orcamento_financeiro WHERE fonte = 'metryx' AND tipo = 'previsao';
        DELETE FROM dim.versao_plano vp
        WHERE vp.fonte = 'metryx' AND vp.codigo = 'previsao-financeiro'
          AND NOT EXISTS (SELECT 1 FROM fato.orcamento_financeiro o WHERE o.versao_plano_id = vp.id)
          AND NOT EXISTS (SELECT 1 FROM fato.mov_animal m WHERE m.versao_plano_id = vp.id)
          AND NOT EXISTS (SELECT 1 FROM fato.rebanho_medio_mensal r WHERE r.versao_plano_id = vp.id)
          AND NOT EXISTS (SELECT 1 FROM fato.area_mensal a WHERE a.versao_plano_id = vp.id);
        UPDATE fato.orcamento_financeiro SET tipo = 'planejamento' WHERE tipo = 'previsao';
        ALTER TABLE fato.orcamento_financeiro ALTER COLUMN tipo SET DEFAULT 'planejamento';
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE fato.orcamento_financeiro ALTER COLUMN tipo SET DEFAULT 'previsao';
        UPDATE fato.orcamento_financeiro SET tipo = 'previsao' WHERE fonte <> 'metryx';
    """)
