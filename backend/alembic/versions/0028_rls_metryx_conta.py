"""rls_metryx_conta

Como a credencial de cada cliente: só o ETL lê o token (o usuário comum não vê a conta; o admin a vê pela política de
escrita, sem a coluna do token).

Revision ID: 0028
Revises: 0027
Create Date: 2026-11-17
"""

from alembic import op

from app.db import rls

revision = "0028"
down_revision = "0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(rls.habilitar("integracao.metryx_conta", None, "tudo"))


def downgrade() -> None:
    op.execute(rls.desabilitar("integracao.metryx_conta"))
