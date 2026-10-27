"""rls_funcao

O cadastro de funções é de referência: todo usuário logado lê, só o admin altera; o ETL não usa.

Revision ID: 0017
Revises: 0016
Create Date: 2026-10-15
"""

from alembic import op

from app.db import rls

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(rls.habilitar("core.funcao", rls.TODOS, "nenhum"))


def downgrade() -> None:
    op.execute(rls.desabilitar("core.funcao"))
