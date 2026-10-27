"""rls_fato: o usuário vê só as fazendas a que tem acesso; só admin e ETL gravam.

Revision ID: 0009
Revises: 0008
Create Date: 2026-10-14
"""

from alembic import op

from app.db import rls

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

TABELAS = [
    "fato.mov_animal",
    "fato.inventario",
    "fato.rebanho_medio_mensal",
    "fato.area_mensal",
    "fato.lancamento_financeiro",
    "fato.orcamento_financeiro",
    "fato.estoque_mensal",
]


def upgrade() -> None:
    for tabela in TABELAS:
        op.execute(rls.habilitar(tabela, rls.por_fazenda(), "tudo"))


def downgrade() -> None:
    for tabela in reversed(TABELAS):
        op.execute(rls.desabilitar(tabela))
