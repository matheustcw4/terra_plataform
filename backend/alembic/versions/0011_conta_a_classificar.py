"""conta_a_classificar: lançamentos e orçamentos apontam para o de-para de contas; conta sem de-para = "A classificar"

Decisão do usuário (14/10/2026, Q1 da validação): conta fora do plano unificado NÃO vai para a quarentena. O lançamento
carrega (o total de receitas/despesas bate com o BI) e aparece como "A classificar" no DRE até o admin classificar.

- dim.plano_contas_map.centro_custo_id passa a aceitar NULL (= pendente) e guarda o texto original da conta;
- fato.lancamento_financeiro / fato.orcamento_financeiro trocam (centro_custo_id, subcentro_id) por plano_contas_map_id:
  classificar a conta reclassifica o histórico sem recarga (mesmo padrão de dim.categoria_map);
- views fato.v_lancamento_financeiro / fato.v_orcamento_financeiro devolvem a classificação resolvida
  (subcentro sobrepõe o centro; pendente = 'A CLASSIFICAR'), com security_invoker para valer o RLS de quem consulta.

Revision ID: 0011
Revises: 0010
Create Date: 2026-10-14
"""

from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

FATOS = ("lancamento_financeiro", "orcamento_financeiro")

VIEW = """
CREATE VIEW fato.v_{tabela} WITH (security_invoker = true) AS
SELECT f.*,
       m.centro_custo_id,
       m.subcentro_id,
       m.centro_custo_id IS NULL                                        AS a_classificar,
       coalesce(c.nome, 'A classificar')                                AS centro_custo,
       sc.nome                                                          AS subcentro,
       coalesce(c.classificacao, 'A CLASSIFICAR')                       AS classificacao,
       coalesce(sc.entra_desembolso, c.entra_desembolso, false)         AS entra_desembolso,
       coalesce(sc.entra_custeio, c.entra_custeio, false)               AS entra_custeio,
       coalesce(sc.tipo_custeio, c.tipo_custeio)                        AS tipo_custeio,
       coalesce(sc.eh_reposicao, c.eh_reposicao, false)                 AS eh_reposicao,
       m.nome_centro_origem,
       m.nome_subcentro_origem
FROM fato.{tabela} f
JOIN dim.plano_contas_map m ON m.id = f.plano_contas_map_id
LEFT JOIN dim.centro_custo c ON c.id = m.centro_custo_id
LEFT JOIN dim.subcentro sc ON sc.id = m.subcentro_id
"""


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE dim.plano_contas_map
            ALTER COLUMN centro_custo_id DROP NOT NULL,
            ADD COLUMN nome_centro_origem    text,
            ADD COLUMN nome_subcentro_origem text,
            ADD COLUMN confirmado_por        uuid REFERENCES core.usuario(id),
            ADD COLUMN confirmado_em         timestamptz,
            ADD COLUMN atualizado_em         timestamptz NOT NULL DEFAULT now(),
            DROP CONSTRAINT plano_contas_map_fonte_check,
            ADD CONSTRAINT ck_plano_contas_map_fonte CHECK (fonte IN ('planilha','metryx','manual')),
            ADD CONSTRAINT ck_plano_contas_map_subcentro CHECK (subcentro_id IS NULL OR centro_custo_id IS NOT NULL);
        COMMENT ON COLUMN dim.plano_contas_map.centro_custo_id IS 'NULL = conta a classificar (pendente do admin)';
        """
    )
    for t in FATOS:
        op.execute(
            f"""
            ALTER TABLE fato.{t} ADD COLUMN plano_contas_map_id uuid REFERENCES dim.plano_contas_map(id);

            -- dados existentes: garante um de-para para cada (fonte, centro, subcentro) já gravado
            INSERT INTO dim.plano_contas_map (fonte, centro_origem, subcentro_origem, centro_custo_id, subcentro_id,
                                              nome_centro_origem, nome_subcentro_origem)
            SELECT DISTINCT f.fonte, c.nome_normalizado, coalesce(sc.nome_normalizado, ''), f.centro_custo_id,
                   f.subcentro_id, c.nome, sc.nome
            FROM fato.{t} f
            JOIN dim.centro_custo c ON c.id = f.centro_custo_id
            LEFT JOIN dim.subcentro sc ON sc.id = f.subcentro_id
            ON CONFLICT ON CONSTRAINT uq_plano_contas_map DO NOTHING;

            UPDATE fato.{t} f SET plano_contas_map_id = (
                SELECT m.id FROM dim.plano_contas_map m
                WHERE m.fonte = f.fonte AND m.centro_custo_id = f.centro_custo_id
                  AND m.subcentro_id IS NOT DISTINCT FROM f.subcentro_id
                ORDER BY m.subcentro_origem DESC LIMIT 1);

            ALTER TABLE fato.{t} ALTER COLUMN plano_contas_map_id SET NOT NULL,
                                 DROP COLUMN centro_custo_id,
                                 DROP COLUMN subcentro_id;
            CREATE INDEX ix_{t}_conta ON fato.{t} (plano_contas_map_id);
            """
        )
        op.execute(VIEW.format(tabela=t))
    op.execute("CREATE INDEX ix_plano_contas_map_pendente ON dim.plano_contas_map (fonte) "
               "WHERE centro_custo_id IS NULL")


def downgrade() -> None:
    op.execute("DROP INDEX dim.ix_plano_contas_map_pendente")
    for t in reversed(FATOS):
        op.execute(
            f"""
            DROP VIEW fato.v_{t};
            ALTER TABLE fato.{t} ADD COLUMN centro_custo_id smallint REFERENCES dim.centro_custo(id),
                                 ADD COLUMN subcentro_id smallint REFERENCES dim.subcentro(id);
            UPDATE fato.{t} f SET centro_custo_id = m.centro_custo_id, subcentro_id = m.subcentro_id
            FROM dim.plano_contas_map m WHERE m.id = f.plano_contas_map_id;
            -- falha de propósito se houver lançamento em conta a classificar (o esquema antigo não o representa)
            ALTER TABLE fato.{t} ALTER COLUMN centro_custo_id SET NOT NULL, DROP COLUMN plano_contas_map_id;
            """
        )
    op.execute(
        """
        DELETE FROM dim.plano_contas_map WHERE centro_custo_id IS NULL;
        ALTER TABLE dim.plano_contas_map
            DROP CONSTRAINT ck_plano_contas_map_subcentro,
            DROP CONSTRAINT ck_plano_contas_map_fonte,
            ADD CONSTRAINT plano_contas_map_fonte_check CHECK (fonte IN ('planilha','metryx')),
            DROP COLUMN atualizado_em, DROP COLUMN confirmado_em, DROP COLUMN confirmado_por,
            DROP COLUMN nome_subcentro_origem, DROP COLUMN nome_centro_origem,
            ALTER COLUMN centro_custo_id SET NOT NULL;
        """
    )
