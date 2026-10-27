"""funcao_pendencias: o que a última carga de cada arquivo deixou de fora ou marcou para conferir, por fazenda.

A tela de pendências mostra ao usuário as linhas da quarentena e os avisos das fazendas dele, com o arquivo de onde
vieram, para ele corrigir na origem. O RLS já deixa o usuário ler a quarentena e os avisos das fazendas que ele vê,
mas não as tabelas de arquivo e versão (ingest.unidade_origem/versao_origem, só admin). Esta função (SECURITY
DEFINER, dona app_owner, o mesmo padrão de app.dados_de_login) junta as três coisas e aplica a mesma regra de
visibilidade do RLS: admin vê tudo; os demais, só as fazendas de app.fazendas_visiveis().

Só entra o diagnóstico da versão vigente de cada arquivo (a última carregada): corrigida a planilha, a carga seguinte
substitui o diagnóstico e a pendência some da tela. Unidade de carga única (o histórico do snapshot do BI, metadado
`carga_unica`) fica de fora: ela não é relida, então não há o que corrigir na origem.

Revision ID: 0013
Revises: 0012
Create Date: 2026-10-15
"""

from alembic import op

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE FUNCTION app.pendencias_de_carga(p_fazendas uuid[])
        RETURNS TABLE (fazenda_id uuid, fazenda text, situacao text, codigo text, detalhe text, origem_linha text,
                       dados jsonb, origem text, eh_arquivo boolean, salvo_em timestamptz, carregado_em timestamptz)
        LANGUAGE sql STABLE SECURITY DEFINER SET search_path = pg_catalog, pg_temp AS
        $$
            WITH fazendas AS (
                SELECT f.id, f.nome
                FROM core.fazenda f
                WHERE f.id = ANY (p_fazendas)
                  AND (app.eh_admin() OR f.id = ANY (app.fazendas_visiveis()))
            ),
            versao_vigente AS (
                -- arquivo = unidade com data de modificação (mesmo critério do aviso de arquivo em dobro)
                SELECT u.ultima_versao_id AS versao_id, coalesce(u.descricao, u.chave) AS origem,
                       u.metadados ? 'mtime' AS eh_arquivo,
                       to_timestamp((u.metadados ->> 'mtime')::double precision) AS salvo_em, v.carregado_em
                FROM ingest.unidade_origem u
                JOIN ingest.versao_origem v ON v.id = u.ultima_versao_id
                WHERE u.status = 'ativa' AND NOT (u.metadados ? 'carga_unica')
            )
            SELECT q.fazenda_id, f.nome, 'nao_entrou', q.codigo, q.motivo, q.origem_linha, q.dados, a.origem,
                   a.eh_arquivo, a.salvo_em, a.carregado_em
            FROM ingest.linha_quarentena q
            JOIN fazendas f ON f.id = q.fazenda_id
            JOIN versao_vigente a ON a.versao_id = q.versao_origem_id
            UNION ALL
            SELECT o.fazenda_id, f.nome, 'confira', o.codigo, o.mensagem, o.origem_linha, o.contexto, a.origem,
                   a.eh_arquivo, a.salvo_em, a.carregado_em
            FROM ingest.ocorrencia o
            JOIN fazendas f ON f.id = o.fazenda_id
            JOIN versao_vigente a ON a.versao_id = o.versao_origem_id
            WHERE o.nivel <> 'info'
        $$;

        REVOKE ALL ON FUNCTION app.pendencias_de_carga(uuid[]) FROM PUBLIC;
        GRANT EXECUTE ON FUNCTION app.pendencias_de_carga(uuid[]) TO app_user;
        """
    )


def downgrade() -> None:
    op.execute("DROP FUNCTION app.pendencias_de_carga(uuid[])")
