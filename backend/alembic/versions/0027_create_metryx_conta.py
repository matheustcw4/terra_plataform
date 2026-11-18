"""create_metryx_conta

A conta mestre do Metryx (pedido do usuário, 17/11/2026): um token que só serve para listar os clientes e o token de
cada um (`GET /api-metryx/customers`, o mesmo que o Pentaho do BI usa). A cada carga a lista é relida e alimenta
`integracao.metryx_credencial`: cliente novo entra sozinho, token trocado é rotacionado.

O token fica cifrado, como o dos clientes: o admin pode cadastrar, mas a coluna do token não tem GRANT de leitura.

Revision ID: 0027
Revises: 0026
Create Date: 2026-11-17
"""

from alembic import op

revision = "0027"
down_revision = "0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE integracao.metryx_conta (
            id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            nome                text NOT NULL,      -- para reconhecer a conta na tela (ex.: "Terra")
            token_cifrado       bytea NOT NULL,
            token_impressao     text NOT NULL,      -- 12 primeiros hex do sha256(token), só p/ auditoria
            status              text NOT NULL DEFAULT 'ativa' CHECK (status IN ('ativa','invalida','revogada')),
            clientes            integer,            -- quantos clientes a última consulta listou
            ultima_validacao_em timestamptz,
            ultimo_erro         text,
            criado_em           timestamptz NOT NULL DEFAULT now(),
            atualizado_em       timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_metryx_conta UNIQUE (token_impressao)
        );
        REVOKE SELECT ON integracao.metryx_conta FROM app_user;
        GRANT SELECT (id, nome, token_impressao, status, clientes, ultima_validacao_em, ultimo_erro, criado_em,
                      atualizado_em) ON integracao.metryx_conta TO app_user;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE integracao.metryx_conta")
