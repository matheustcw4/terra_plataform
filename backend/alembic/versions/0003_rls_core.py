"""rls_core

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-14
"""

from alembic import op

from app.db import rls

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

TABELAS = {
    "core.cliente": (rls.por_cliente("id"), "tudo"),
    "core.fazenda": (rls.por_fazenda("id"), "tudo"),
    "core.retiro": (rls.por_fazenda(), "tudo"),
    # usuário lê o próprio cadastro; o ETL não enxerga usuários
    "core.usuario": (f"{rls.ADMIN} OR id = app.usuario_id()", "nenhum"),
    "core.usuario_fazenda": (f"{rls.ADMIN} OR usuario_id = app.usuario_id()", "nenhum"),
    "core.fonte_vinculo": (None, "tudo"),
    "core.fazenda_fonte": (rls.por_fazenda(), "tudo"),
}


def upgrade() -> None:
    for tabela, (leitura, etl) in TABELAS.items():
        op.execute(rls.habilitar(tabela, leitura, etl))


def downgrade() -> None:
    for tabela in reversed(TABELAS):
        op.execute(rls.desabilitar(tabela))
