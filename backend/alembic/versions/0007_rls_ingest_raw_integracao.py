"""rls_ingest_raw_integracao

Jobs e versões: só admin (via API) e ETL. Ocorrências e quarentena: o usuário vê as das suas fazendas.
Bruto e credenciais: só o ETL lê (credencial: o admin grava, mas a coluna do token não tem GRANT de leitura).

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-14
"""

from alembic import op

from app.db import rls

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

TABELAS = {
    "ingest.job": (None, "tudo"),
    "ingest.unidade_origem": (None, "tudo"),
    "ingest.versao_origem": (None, "tudo"),
    "ingest.ocorrencia": (f"{rls.ADMIN} OR (fazenda_id IS NOT NULL AND fazenda_id = ANY ((SELECT app.fazendas_visiveis())::uuid[]))",
                          "tudo"),
    "ingest.linha_quarentena": (
        f"{rls.ADMIN} OR (fazenda_id IS NOT NULL AND fazenda_id = ANY ((SELECT app.fazendas_visiveis())::uuid[]))", "tudo"
    ),
    "raw.payload": (None, "tudo"),
    "integracao.metryx_credencial": (None, "tudo"),
}


def upgrade() -> None:
    for tabela, (leitura, etl) in TABELAS.items():
        op.execute(rls.habilitar(tabela, leitura, etl))


def downgrade() -> None:
    for tabela in reversed(TABELAS):
        op.execute(rls.desabilitar(tabela))
