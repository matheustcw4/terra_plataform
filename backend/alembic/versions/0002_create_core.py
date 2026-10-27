"""create_core: cliente, fazenda, retiro, usuario, usuario_fazenda, fonte_vinculo, fazenda_fonte + funções de acesso

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-14
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

DOMINIOS = (
    "'pecuario_realizado','pecuario_planejado','rebanho_medio_realizado','rebanho_medio_planejado',"
    "'area_realizado','area_planejado','financeiro_realizado','financeiro_planejado'"
)


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE core.cliente (
            id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            codigo        integer UNIQUE,              -- código do cliente na consultoria (planilha: fUnidade!D2)
            nome          text NOT NULL,
            ativo         boolean NOT NULL DEFAULT true,
            criado_em     timestamptz NOT NULL DEFAULT now(),
            atualizado_em timestamptz NOT NULL DEFAULT now()
        );

        CREATE TABLE core.fazenda (
            id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            cliente_id        uuid NOT NULL REFERENCES core.cliente(id),
            nome              text NOT NULL,
            proprietario      text,                    -- atributo, nunca chave
            sistema_produtivo text CHECK (sistema_produtivo IN ('CRIA','RECRIA E ENGORDA','CICLO COMPLETO')),
            tipo_ano          text CHECK (tipo_ano IN ('CIVIL','SAFRA')),
            ativo             boolean NOT NULL DEFAULT true,
            criado_em         timestamptz NOT NULL DEFAULT now(),
            atualizado_em     timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_fazenda_cliente ON core.fazenda (cliente_id);

        CREATE TABLE core.retiro (
            id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fazenda_id uuid NOT NULL REFERENCES core.fazenda(id) ON DELETE CASCADE,
            nome       text NOT NULL,
            ativo      boolean NOT NULL DEFAULT true,
            criado_em  timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_retiro_fazenda ON core.retiro (fazenda_id);

        CREATE TABLE core.usuario (
            id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            email         text NOT NULL,
            nome          text NOT NULL,
            senha_hash    text,
            eh_admin      boolean NOT NULL DEFAULT false,
            ativo         boolean NOT NULL DEFAULT true,
            criado_em     timestamptz NOT NULL DEFAULT now(),
            atualizado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_usuario_email_normalizado CHECK (email = lower(btrim(email)))
        );
        CREATE UNIQUE INDEX uq_usuario_email ON core.usuario (email);

        -- Acesso por usuário: N:N (um usuário vê várias fazendas; uma fazenda é vista por vários usuários).
        CREATE TABLE core.usuario_fazenda (
            usuario_id uuid NOT NULL REFERENCES core.usuario(id) ON DELETE CASCADE,
            fazenda_id uuid NOT NULL REFERENCES core.fazenda(id) ON DELETE CASCADE,
            papel      text NOT NULL DEFAULT 'cliente'
                       CHECK (papel IN ('cliente','tecnico','gerente','regional','consultor')),
            criado_em  timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (usuario_id, fazenda_id)
        );
        CREATE INDEX ix_usuario_fazenda_fazenda ON core.usuario_fazenda (fazenda_id);

        -- De-para de identidade: id externo da fonte -> id interno. Nada é casado por nome.
        CREATE TABLE core.fonte_vinculo (
            id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fonte         text NOT NULL CHECK (fonte IN ('planilha','metryx')),
            entidade      text NOT NULL CHECK (entidade IN ('cliente','fazenda','retiro')),
            id_externo    text NOT NULL,
            entidade_id   uuid NOT NULL,
            nome_externo  text,
            criado_em     timestamptz NOT NULL DEFAULT now(),
            atualizado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_fonte_vinculo UNIQUE (fonte, entidade, id_externo)
        );
        CREATE INDEX ix_fonte_vinculo_entidade ON core.fonte_vinculo (entidade, entidade_id);
        """
    )
    op.execute(
        f"""
        -- Qual fonte é a ativa para cada domínio de cada fazenda (clientes híbridos; evita dupla contagem).
        CREATE TABLE core.fazenda_fonte (
            fazenda_id    uuid NOT NULL REFERENCES core.fazenda(id) ON DELETE CASCADE,
            dominio       text NOT NULL CHECK (dominio IN ({DOMINIOS})),
            fonte         text NOT NULL CHECK (fonte IN ('planilha','metryx','manual')),
            atualizado_em timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (fazenda_id, dominio)
        );
        """
    )
    # Funções de acesso: SECURITY DEFINER (dono app_owner, BYPASSRLS) para ler as tabelas de acesso sem recursão de RLS.
    op.execute(
        """
        CREATE FUNCTION app.eh_admin() RETURNS boolean
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS
        $$ SELECT coalesce((SELECT u.eh_admin FROM core.usuario u
                            WHERE u.id = app.usuario_id() AND u.ativo), false) $$;

        CREATE FUNCTION app.fazendas_visiveis() RETURNS uuid[]
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS
        $$ SELECT coalesce(array_agg(uf.fazenda_id), '{}')
           FROM core.usuario_fazenda uf JOIN core.usuario u ON u.id = uf.usuario_id
           WHERE uf.usuario_id = app.usuario_id() AND u.ativo $$;

        CREATE FUNCTION app.clientes_visiveis() RETURNS uuid[]
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS
        $$ SELECT coalesce(array_agg(DISTINCT f.cliente_id), '{}')
           FROM core.fazenda f WHERE f.id = ANY (app.fazendas_visiveis()) $$;

        REVOKE ALL ON FUNCTION app.eh_admin(), app.fazendas_visiveis(), app.clientes_visiveis() FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.eh_admin(), app.fazendas_visiveis(), app.clientes_visiveis()
            TO app_user, app_etl;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP FUNCTION app.clientes_visiveis();
        DROP FUNCTION app.fazendas_visiveis();
        DROP FUNCTION app.eh_admin();
        DROP TABLE core.fazenda_fonte;
        DROP TABLE core.fonte_vinculo;
        DROP TABLE core.usuario_fazenda;
        DROP TABLE core.usuario;
        DROP TABLE core.retiro;
        DROP TABLE core.fazenda;
        DROP TABLE core.cliente;
        """
    )
