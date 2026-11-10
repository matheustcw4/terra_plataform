"""rls_centro_custo_fonte

Dimensão de referência, como `dim.centro_custo`: todo usuário lê (as views dos lançamentos são security_invoker e
juntam esta tabela), só o admin altera, o ETL só lê.

Revision ID: 0023
Revises: 0022
Create Date: 2026-11-10
"""

from alembic import op

from app.db import rls

revision = "0023"
down_revision = "0022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(rls.habilitar("dim.centro_custo_fonte", rls.TODOS, "leitura"))


def downgrade() -> None:
    op.execute(rls.desabilitar("dim.centro_custo_fonte"))
