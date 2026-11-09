"""create_importacao: as planilhas enviadas pela tela, na fila do worker (pedido do usuário, 09/11/2026)

A tela de importação substitui a pasta sincronizada com o Google Drive (D8): o técnico envia o RELATÓRIO*.xlsm, a API
guarda o arquivo aqui e o worker o carrega pelo mesmo motor da pasta (mesma unidade de origem, pelo nome do arquivo).
O arquivo fica na tabela só até ser processado: depois disso o que vale é o bruto lido (raw.payload), que permite
reprocessar sem o arquivo. Quem enviou, quando, o resultado e as fazendas alimentadas ficam para o histórico da tela.

`enviado_por` guarda o nome de quem enviou: com o RLS, um técnico não lê o cadastro dos outros usuários, mas vê as
importações das fazendas dele feitas por outra pessoa.

Revision ID: 0020
Revises: 0019
Create Date: 2026-11-09
"""

from alembic import op

revision = "0020"
down_revision = "0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE ingest.importacao (
            id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            usuario_id       uuid REFERENCES core.usuario(id) ON DELETE SET NULL,
            enviado_por      text NOT NULL,
            arquivo          text NOT NULL,
            sha256           text NOT NULL,
            tamanho_bytes    bigint NOT NULL,
            conteudo         bytea,
            status           text NOT NULL DEFAULT 'na_fila',
            mensagem         text,
            avisos           integer NOT NULL DEFAULT 0,
            quarentena       integer NOT NULL DEFAULT 0,
            fazendas         uuid[] NOT NULL DEFAULT '{}',
            job_id           uuid REFERENCES ingest.job(id) ON DELETE SET NULL,
            versao_origem_id uuid REFERENCES ingest.versao_origem(id) ON DELETE SET NULL,
            enviado_em       timestamptz NOT NULL DEFAULT now(),
            iniciado_em      timestamptz,
            finalizado_em    timestamptz,
            CONSTRAINT ck_importacao_status CHECK (status IN (
                'na_fila', 'processando', 'carregada', 'carregada_com_avisos', 'inalterada', 'ignorada', 'erro')),
            -- o arquivo só fica enquanto espera o worker
            CONSTRAINT ck_importacao_conteudo CHECK (conteudo IS NOT NULL OR status NOT IN ('na_fila', 'processando'))
        );
        CREATE INDEX ix_importacao_fila ON ingest.importacao (enviado_em) WHERE status IN ('na_fila', 'processando');
        CREATE INDEX ix_importacao_enviado_em ON ingest.importacao (enviado_em DESC);
        CREATE INDEX ix_importacao_fazendas ON ingest.importacao USING gin (fazendas);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE ingest.importacao")
