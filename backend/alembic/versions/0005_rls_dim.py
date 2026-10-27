"""rls_dim

Dimensões de referência são globais: todo usuário lê, só admin altera, o ETL só lê.
De-paras ligados a cliente/fazenda seguem a visibilidade do usuário; o ETL grava.

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-14
"""

from alembic import op

from app.db import rls

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None

TABELAS = {
    "dim.categoria_bi": (rls.TODOS, "leitura"),
    "dim.centro_custo": (rls.TODOS, "leitura"),
    "dim.subcentro": (rls.TODOS, "leitura"),
    "dim.calendario": (rls.TODOS, "leitura"),
    "dim.parametro": (rls.TODOS, "leitura"),
    "dim.plano_contas_map": (rls.TODOS, "tudo"),
    "dim.categoria_map": (f"{rls.por_fazenda()} OR cliente_id = ANY ((SELECT app.clientes_visiveis())::uuid[])", "tudo"),
    "dim.versao_plano": (rls.por_cliente(), "tudo"),
}


def upgrade() -> None:
    for tabela, (leitura, etl) in TABELAS.items():
        op.execute(rls.habilitar(tabela, leitura, etl))


def downgrade() -> None:
    for tabela in reversed(TABELAS):
        op.execute(rls.desabilitar(tabela))
