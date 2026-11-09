"""rls_importacao

Todo usuário logado envia planilhas, mas só em nome dele e só para a fila (`usuario_envio`); quem altera ou apaga uma
importação é o admin ou o worker. Cada um lê as que enviou e as das fazendas que vê (um colega pode ter importado a
planilha de uma fazenda que os dois acompanham); o admin lê todas. A permissão de alimentar a fazenda do arquivo é
conferida pelo worker, com a mesma regra do RLS (app.eh_admin e app.fazendas_visiveis de quem enviou).

Revision ID: 0021
Revises: 0020
Create Date: 2026-11-09
"""

from alembic import op

from app.db import rls

revision = "0021"
down_revision = "0020"
branch_labels = None
depends_on = None

TABELA = "ingest.importacao"
LEITURA = (f"{rls.ADMIN} OR usuario_id = (SELECT app.usuario_id()) "
           "OR fazendas && (SELECT app.fazendas_visiveis())::uuid[]")


def upgrade() -> None:
    op.execute(rls.habilitar(TABELA, LEITURA, "tudo"))
    op.execute(f"""
        CREATE POLICY usuario_envio ON {TABELA} FOR INSERT TO app_user
            WITH CHECK (usuario_id = (SELECT app.usuario_id()) AND status = 'na_fila');
    """)


def downgrade() -> None:
    op.execute(f"DROP POLICY IF EXISTS usuario_envio ON {TABELA}")
    op.execute(rls.desabilitar(TABELA))
