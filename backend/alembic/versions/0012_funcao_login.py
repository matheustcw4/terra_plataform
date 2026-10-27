"""funcao_login: dados de login de um usuário pelo e-mail, para a API (que roda como app_user, sob RLS).

Antes do login ainda não há usuário no contexto, e o RLS de core.usuario só deixa cada um ler a própria linha. Esta
função (SECURITY DEFINER, dona app_owner) devolve só o necessário para conferir a senha — o mesmo padrão de
app.eh_admin(). A senha é conferida na API (argon2), nunca no banco.

Revision ID: 0012
Revises: 0011
Create Date: 2026-10-15
"""

from alembic import op

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION app.dados_de_login(p_email text)
        RETURNS TABLE (id uuid, nome text, senha_hash text, eh_admin boolean, ativo boolean)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS
        $$ SELECT u.id, u.nome, u.senha_hash, u.eh_admin, u.ativo
           FROM core.usuario u
           WHERE u.email = lower(btrim(p_email)) $$;

        REVOKE ALL ON FUNCTION app.dados_de_login(text) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.dados_de_login(text) TO app_user;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION app.dados_de_login(text)")
