"""create_ingest_raw_integracao: job, unidade_origem, versao_origem, ocorrencia, linha_quarentena, raw.payload,
integracao.metryx_credencial

Uma "unidade de origem" é o que um adapter descobre e extrai (um arquivo .xlsm; um par cliente × endpoint Metryx).
Cada conteúdo distinto (sha256) vira uma "versão de origem"; todo fato aponta para a versão de onde veio (origem_ref).

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-14
"""

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE ingest.job (
            id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fonte               text NOT NULL CHECK (fonte IN ('planilha','metryx','manual')),
            tipo                text NOT NULL,                 -- carga | reprocessamento | recalculo
            status              text NOT NULL DEFAULT 'pendente'
                                CHECK (status IN ('pendente','processando','concluido','concluido_com_avisos','erro')),
            usuario_id          uuid REFERENCES core.usuario(id) ON DELETE SET NULL,
            parametros          jsonb,
            detalhe             jsonb,                          -- resumo por unidade, alertas
            unidades_total      integer NOT NULL DEFAULT 0,
            unidades_carregadas integer NOT NULL DEFAULT 0,
            unidades_inalteradas integer NOT NULL DEFAULT 0,
            unidades_com_erro   integer NOT NULL DEFAULT 0,
            criado_em           timestamptz NOT NULL DEFAULT now(),
            iniciado_em         timestamptz,
            finalizado_em       timestamptz
        );
        CREATE INDEX ix_job_criado_em ON ingest.job (criado_em DESC);

        CREATE TABLE ingest.unidade_origem (
            id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fonte             text NOT NULL CHECK (fonte IN ('planilha','metryx','manual')),
            chave             text NOT NULL,          -- planilha: caminho NFC; Metryx: '<idCustomer>:<endpoint>'
            descricao         text,
            metadados         jsonb,                  -- tamanho, mtime, drive_file_id, endpoint…
            assinatura        text,                   -- impressão rápida (ex.: tamanho+mtime) p/ pular sem ler
            status            text NOT NULL DEFAULT 'ativa' CHECK (status IN ('ativa','removida','ignorada')),
            ultima_versao_id  uuid,                   -- última versão carregada com sucesso
            primeiro_visto_em timestamptz NOT NULL DEFAULT now(),
            ultimo_visto_em   timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_unidade_origem UNIQUE (fonte, chave)
        );

        CREATE TABLE ingest.versao_origem (
            id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            unidade_id    uuid NOT NULL REFERENCES ingest.unidade_origem(id) ON DELETE CASCADE,
            sha256        text NOT NULL,
            tamanho_bytes bigint,
            metadados     jsonb,
            status        text NOT NULL DEFAULT 'extraida'
                          CHECK (status IN ('extraida','carregada','carregada_com_avisos','erro','substituida')),
            job_id        uuid REFERENCES ingest.job(id) ON DELETE SET NULL,
            criado_em     timestamptz NOT NULL DEFAULT now(),
            carregado_em  timestamptz,
            CONSTRAINT uq_versao_origem UNIQUE (unidade_id, sha256)
        );
        ALTER TABLE ingest.unidade_origem
            ADD CONSTRAINT fk_unidade_ultima_versao FOREIGN KEY (ultima_versao_id)
            REFERENCES ingest.versao_origem(id) ON DELETE SET NULL;

        CREATE TABLE ingest.ocorrencia (
            id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id           uuid REFERENCES ingest.job(id) ON DELETE CASCADE,
            versao_origem_id uuid REFERENCES ingest.versao_origem(id) ON DELETE CASCADE,
            fazenda_id       uuid REFERENCES core.fazenda(id) ON DELETE CASCADE,
            nivel            text NOT NULL CHECK (nivel IN ('erro','aviso','info')),
            codigo           text NOT NULL,
            mensagem         text NOT NULL,
            entidade         text,
            origem_linha     text,
            contexto         jsonb,
            criado_em        timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_ocorrencia_versao ON ingest.ocorrencia (versao_origem_id);
        CREATE INDEX ix_ocorrencia_fazenda ON ingest.ocorrencia (fazenda_id, criado_em DESC);

        -- Linhas que não puderam ser carregadas (o resto do arquivo/payload carrega normalmente).
        CREATE TABLE ingest.linha_quarentena (
            id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            versao_origem_id uuid NOT NULL REFERENCES ingest.versao_origem(id) ON DELETE CASCADE,
            job_id           uuid REFERENCES ingest.job(id) ON DELETE SET NULL,
            fazenda_id       uuid REFERENCES core.fazenda(id) ON DELETE CASCADE,
            entidade         text NOT NULL,
            origem_linha     text,
            codigo           text NOT NULL,
            motivo           text NOT NULL,
            dados            jsonb NOT NULL,
            criado_em        timestamptz NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_quarentena_versao ON ingest.linha_quarentena (versao_origem_id);
        CREATE INDEX ix_quarentena_fazenda ON ingest.linha_quarentena (fazenda_id);

        -- Conteúdo bruto JSON (Metryx), fiel à origem: permite reprocessar sem chamar a API.
        CREATE TABLE raw.payload (
            id               uuid NOT NULL DEFAULT gen_random_uuid(),
            recebido_em      timestamptz NOT NULL DEFAULT now(),
            versao_origem_id uuid NOT NULL REFERENCES ingest.versao_origem(id) ON DELETE CASCADE,
            fonte            text NOT NULL,
            endpoint         text,
            http_status      integer,
            qtd_itens        integer,
            conteudo         jsonb NOT NULL,
            PRIMARY KEY (recebido_em, id)
        ) PARTITION BY RANGE (recebido_em);
        -- TODO: partições mensais + retenção (manter sempre a última por unidade); por ora tudo cai na padrão.
        CREATE TABLE raw.payload_padrao PARTITION OF raw.payload DEFAULT;
        -- acesso só pela tabela-mãe (onde está o RLS); privilégios na partição driblariam as políticas
        REVOKE ALL ON raw.payload_padrao FROM app_user, app_etl;
        CREATE INDEX ix_payload_versao ON raw.payload (versao_origem_id);

        -- Tokens Metryx: cifrados (a chave fica fora do banco). app_user (admin) grava, mas não lê o token.
        CREATE TABLE integracao.metryx_credencial (
            id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            cliente_id          uuid NOT NULL REFERENCES core.cliente(id) ON DELETE CASCADE,
            metryx_customer_id  text NOT NULL,      -- idCustomer esperado nos payloads
            token_cifrado       bytea NOT NULL,
            token_impressao     text NOT NULL,      -- 12 primeiros hex do sha256(token), só p/ auditoria
            status              text NOT NULL DEFAULT 'ativa' CHECK (status IN ('ativa','invalida','revogada')),
            ultima_validacao_em timestamptz,
            ultimo_erro         text,
            criado_em           timestamptz NOT NULL DEFAULT now(),
            atualizado_em       timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_metryx_credencial UNIQUE (cliente_id, token_impressao)
        );
        REVOKE SELECT ON integracao.metryx_credencial FROM app_user;
        GRANT SELECT (id, cliente_id, metryx_customer_id, token_impressao, status, ultima_validacao_em, ultimo_erro,
                      criado_em, atualizado_em) ON integracao.metryx_credencial TO app_user;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE integracao.metryx_credencial;
        DROP TABLE raw.payload;
        DROP TABLE ingest.linha_quarentena;
        DROP TABLE ingest.ocorrencia;
        ALTER TABLE ingest.unidade_origem DROP CONSTRAINT fk_unidade_ultima_versao;
        DROP TABLE ingest.versao_origem;
        DROP TABLE ingest.unidade_origem;
        DROP TABLE ingest.job;
        """
    )
