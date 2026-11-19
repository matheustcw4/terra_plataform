"""classificacao_outros_creditos: a classificação "Outros créditos" do Metryx no grupo E do DRE

A carga da Estância Nova (19/11/2026, o primeiro cliente que veio pela conta mestre) trouxe a classificação
"Outros créditos", que a migração 0029 não semeava: ela chegava pendente (aviso CLASSIFICATION_UNMAPPED) e as linhas
usavam a classificação da conta. Vai para "E - OUTROS CRÉDITOS", fora do custeio; a marca de desembolso segue a do
Metryx. Só preenche quando a classificação ainda não tem grupo: a que alguém já ligou fica.

Revision ID: 0031
Revises: 0030
Create Date: 2026-11-19
"""

from alembic import op

revision = "0031"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO dim.classificacao_map (fonte, nome_origem, classificacao, entra_custeio, entra_desembolso)
        VALUES ('metryx', 'Outros créditos', 'E - OUTROS CRÉDITOS', false, false)
        ON CONFLICT ON CONSTRAINT uq_classificacao_map DO UPDATE
            SET classificacao = EXCLUDED.classificacao, entra_custeio = EXCLUDED.entra_custeio,
                atualizado_em = now()
            WHERE dim.classificacao_map.classificacao IS NULL;
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE dim.classificacao_map SET classificacao = NULL, entra_custeio = NULL, atualizado_em = now()
        WHERE fonte = 'metryx' AND nome_normalizado = 'OUTROS CREDITOS';
    """)
