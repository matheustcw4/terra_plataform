"""rls_filtros_do_financeiro

Como as outras dimensões (migração 0005): o tipo de atividade é referência global (todos leem, só o admin altera, o
ETL só lê); os de-paras de atividade e de classificação são globais e o ETL grava os nomes novos; a conta bancária é
de um cliente e segue a visibilidade do usuário.

Revision ID: 0030
Revises: 0029
Create Date: 2026-11-18
"""

from alembic import op

from app.db import rls

revision = "0030"
down_revision = "0029"
branch_labels = None
depends_on = None

TABELAS = {
    "dim.tipo_atividade": (rls.TODOS, "leitura"),
    "dim.atividade_map": (rls.TODOS, "tudo"),
    "dim.classificacao_map": (rls.TODOS, "tudo"),
    "dim.conta_bancaria": (rls.por_cliente(), "tudo"),
}


def upgrade() -> None:
    for tabela, (leitura, etl) in TABELAS.items():
        op.execute(rls.habilitar(tabela, leitura, etl))


def downgrade() -> None:
    for tabela in reversed(TABELAS):
        op.execute(rls.desabilitar(tabela))
