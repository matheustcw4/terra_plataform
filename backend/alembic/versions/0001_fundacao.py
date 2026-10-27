"""fundacao: schemas, extensões, privilégios padrão e funções utilitárias

Revision ID: 0001
Revises:
Create Date: 2026-10-14
"""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

SCHEMAS = ["app", "core", "dim", "fato", "mart", "ingest", "raw", "integracao", "compat"]
# schemas com tabelas de negócio acessadas pela API e pelos workers
SCHEMAS_DADOS = ["core", "dim", "fato", "mart", "ingest", "raw", "integracao", "compat"]


def upgrade() -> None:
    for s in SCHEMAS:
        op.execute(f"CREATE SCHEMA {s}")
        op.execute(f"GRANT USAGE ON SCHEMA {s} TO app_user, app_etl")

    # unaccent no schema app (referenciado com nome qualificado nas funções)
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent SCHEMA app")

    for s in SCHEMAS_DADOS:
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA {s} "
            "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user, app_etl"
        )
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA {s} "
            "GRANT USAGE, SELECT ON SEQUENCES TO app_user, app_etl"
        )

    # Usuário do contexto RLS (definido por transação pelo listener after_begin).
    op.execute(
        """
        CREATE FUNCTION app.usuario_id() RETURNS uuid
        LANGUAGE sql STABLE AS
        $$ SELECT nullif(current_setting('app.usuario_id', true), '')::uuid $$
        """
    )
    # Forma normalizada de textos de origem (de-para): sem acento, maiúsculas, espaços colapsados.
    op.execute(
        """
        CREATE FUNCTION app.normalizar(texto text) RETURNS text
        LANGUAGE sql IMMUTABLE PARALLEL SAFE AS
        $$ SELECT nullif(upper(btrim(regexp_replace(
                 app.unaccent('app.unaccent'::regdictionary, replace(texto, chr(160), ' ')),
                 '\\s+', ' ', 'g'))), '') $$
        """
    )


def downgrade() -> None:
    for s in reversed(SCHEMAS_DADOS):
        op.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA {s} REVOKE ALL ON TABLES FROM app_user, app_etl")
        op.execute(
            f"ALTER DEFAULT PRIVILEGES FOR ROLE app_owner IN SCHEMA {s} REVOKE ALL ON SEQUENCES FROM app_user, app_etl"
        )
    op.execute("DROP FUNCTION app.normalizar(text)")
    op.execute("DROP FUNCTION app.usuario_id()")
    op.execute("DROP EXTENSION unaccent")
    for s in reversed(SCHEMAS):
        op.execute(f"DROP SCHEMA {s}")
