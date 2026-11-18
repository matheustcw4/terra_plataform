"""create_filtros_do_financeiro: atividade, classificação da fonte e conta bancária dos lançamentos e do orçamento

Três filtros novos das páginas do financeiro (pedido do usuário, 18/11/2026):
- tipo de atividade: o plano do Metryx traz o tipo (`typeActivity`, hoje sempre "Pecuária"), e o realizado e a
  previsão financeira, a atividade (`activity`: "Pecuária Campo", "Agricultura Permanente"…). O filtro é pelo tipo nos
  dois lados (decisão do usuário): cada nome da fonte entra no seu tipo por um de-para (`dim.atividade_map`) que o
  admin classifica; nome novo nasce pendente ("A classificar"), e a linha sem atividade é "Sem atividade";
- classificação: para os dados do Metryx vale 100% a classificação do Metryx (decisão do usuário): Custeio,
  Investimento em fazenda, Investimento em rebanho, Outros débitos, Receitas operacionais, Dividendos, com a marca de
  desembolso (`classificationAnalyticDisbursement`). Ela decide o grupo do DRE e as marcas de custeio e desembolso,
  antes da exceção da fonte e das marcas do centro (`dim.centro_custo_fonte`, `dim.centro_custo`). O plano e a
  previsão trazem a classificação; o realizado não, e o adapter a leva pelo centro de custo do mesmo cliente. Sem
  classificação da fonte (a planilha, ou o centro que nunca aparece no plano), vale a da conta, como antes;
- conta bancária: só o realizado do Metryx tem (`idBankAccount`, `banckAccount`); o plano não é vinculado a conta, e o
  filtro só recorta o realizado.

As views do financeiro ganham `tipo_atividade`, `atividade` e `classificacao_analitica` (o rótulo do filtro: o nome da
fonte ou, sem ele, o grupo do DRE por extenso). Nenhum KPI olha a fonte: a diferença fica no de-para.

Revision ID: 0029
Revises: 0028
Create Date: 2026-11-18
"""

from alembic import op

revision = "0029"
down_revision = "0028"
branch_labels = None
depends_on = None

TIPOS_DE_ATIVIDADE = ("Pecuária", "Agricultura", "Silvicultura", "Outras atividades")

# nome do Metryx -> tipo. Armazém, Financiamento e Imobiliária / Arrendamento chegam pendentes: o admin decide.
ATIVIDADES_DO_METRYX = {
    "Pecuária": "Pecuária",                 # o typeActivity do plano
    "Pecuária Campo": "Pecuária",
    "Pecuária Confinamento": "Pecuária",
    "Pecuária Genética": "Pecuária",
    "Agricultura": "Agricultura",
    "Agricultura Permanente": "Agricultura",
    "Agricultura Anual": "Agricultura",
    "Silvicultura": "Silvicultura",
}

# classificação do Metryx -> grupo do DRE, custeio e desembolso (a marca de desembolso é a do Metryx; custeio =
# desembolso − investimentos, como o relatório financeiro do Metryx)
CLASSIFICACOES_DO_METRYX = {
    "Custeio": ("D - CUSTEIO", True, True),
    "Investimento em fazenda": ("C - INVESTIMENTOS", False, True),
    "Investimento em rebanho": ("C - INVESTIMENTOS", False, False),
    "Outros débitos": ("F - OUTROS DÉBITOS", False, False),
    "Dividendos": ("F - OUTROS DÉBITOS", False, False),
    "Receitas operacionais": ("A - RECEITAS", False, False),
}

GRUPOS_DO_DRE = ("A - RECEITAS", "C - INVESTIMENTOS", "D - CUSTEIO", "E - OUTROS CRÉDITOS", "F - OUTROS DÉBITOS",
                 "NEUTRO")

# o rótulo do filtro de classificação quando a fonte não classifica: o grupo do DRE por extenso
ROTULO_DO_GRUPO = """CASE coalesce(c.classificacao, 'A CLASSIFICAR')
                WHEN 'A - RECEITAS' THEN 'Receitas'
                WHEN 'C - INVESTIMENTOS' THEN 'Investimentos'
                WHEN 'D - CUSTEIO' THEN 'Custeio'
                WHEN 'E - OUTROS CRÉDITOS' THEN 'Outros créditos'
                WHEN 'F - OUTROS DÉBITOS' THEN 'Outros débitos'
                WHEN 'NEUTRO' THEN 'Neutro'
                ELSE 'A classificar' END"""

VIEW = f"""
CREATE VIEW fato.v_{{tabela}} WITH (security_invoker = true) AS
SELECT f.*,
       m.centro_custo_id,
       m.subcentro_id,
       m.centro_custo_id IS NULL                                                     AS a_classificar,
       coalesce(c.nome, 'A classificar')                                             AS centro_custo,
       sc.nome                                                                       AS subcentro,
       coalesce(cm.classificacao, c.classificacao, 'A CLASSIFICAR')                  AS classificacao,
       coalesce(cm.entra_desembolso, r.entra_desembolso, sc.entra_desembolso, c.entra_desembolso, false)
                                                                                     AS entra_desembolso,
       coalesce(cm.entra_custeio, r.entra_custeio, sc.entra_custeio, c.entra_custeio, false) AS entra_custeio,
       coalesce(sc.tipo_custeio, c.tipo_custeio)                                     AS tipo_custeio,
       coalesce(r.eh_reposicao, sc.eh_reposicao, c.eh_reposicao, false)              AS eh_reposicao,
       m.nome_centro_origem,
       m.nome_subcentro_origem,
       coalesce(cm.nome_origem, {ROTULO_DO_GRUPO})                                   AS classificacao_analitica,
       CASE WHEN f.atividade_map_id IS NULL THEN 'Sem atividade'
            ELSE coalesce(ta.nome, 'A classificar') END                              AS tipo_atividade,
       am.nome_origem                                                                AS atividade
FROM fato.{{tabela}} f
JOIN dim.plano_contas_map m ON m.id = f.plano_contas_map_id
LEFT JOIN dim.centro_custo c ON c.id = m.centro_custo_id
LEFT JOIN dim.subcentro sc ON sc.id = m.subcentro_id
LEFT JOIN dim.centro_custo_fonte r ON r.fonte = f.fonte AND r.centro_custo_id = m.centro_custo_id
-- a classificação da fonte só vale depois de ligada a um grupo do DRE; pendente, vale a da conta
LEFT JOIN dim.classificacao_map cm ON cm.id = f.classificacao_map_id AND cm.classificacao IS NOT NULL
LEFT JOIN dim.atividade_map am ON am.id = f.atividade_map_id
LEFT JOIN dim.tipo_atividade ta ON ta.id = am.tipo_atividade_id
"""

# as da migração 0024 (lançamentos) e 0022 (orçamento), para o downgrade
VIEW_ANTERIOR = """
CREATE VIEW fato.v_{tabela} WITH (security_invoker = true) AS
SELECT f.*,
       m.centro_custo_id,
       m.subcentro_id,
       m.centro_custo_id IS NULL                                                     AS a_classificar,
       coalesce(c.nome, 'A classificar')                                             AS centro_custo,
       sc.nome                                                                       AS subcentro,
       coalesce(c.classificacao, 'A CLASSIFICAR')                                    AS classificacao,
       coalesce(r.entra_desembolso, sc.entra_desembolso, c.entra_desembolso, false)  AS entra_desembolso,
       coalesce(r.entra_custeio, sc.entra_custeio, c.entra_custeio, false)           AS entra_custeio,
       coalesce(sc.tipo_custeio, c.tipo_custeio)                                     AS tipo_custeio,
       coalesce(r.eh_reposicao, sc.eh_reposicao, c.eh_reposicao, false)              AS eh_reposicao,
       m.nome_centro_origem,
       m.nome_subcentro_origem
FROM fato.{tabela} f
JOIN dim.plano_contas_map m ON m.id = f.plano_contas_map_id
LEFT JOIN dim.centro_custo c ON c.id = m.centro_custo_id
LEFT JOIN dim.subcentro sc ON sc.id = m.subcentro_id
LEFT JOIN dim.centro_custo_fonte r ON r.fonte = f.fonte AND r.centro_custo_id = m.centro_custo_id
"""

FATOS = ("lancamento_financeiro", "orcamento_financeiro")


def upgrade() -> None:
    for tabela in FATOS:
        op.execute(f"DROP VIEW fato.v_{tabela};")
    criar_as_dimensoes()
    semear_as_dimensoes()
    op.execute("""
        ALTER TABLE fato.lancamento_financeiro
            ADD COLUMN atividade_map_id     smallint REFERENCES dim.atividade_map(id),
            ADD COLUMN classificacao_map_id smallint REFERENCES dim.classificacao_map(id),
            ADD COLUMN conta_bancaria_id    uuid REFERENCES dim.conta_bancaria(id);
        ALTER TABLE fato.orcamento_financeiro
            ADD COLUMN atividade_map_id     smallint REFERENCES dim.atividade_map(id),
            ADD COLUMN classificacao_map_id smallint REFERENCES dim.classificacao_map(id);
        CREATE INDEX ix_lancamento_conta_bancaria ON fato.lancamento_financeiro (conta_bancaria_id)
            WHERE conta_bancaria_id IS NOT NULL;
    """)
    for tabela in FATOS:
        op.execute(VIEW.format(tabela=tabela))


def criar_as_dimensoes() -> None:
    grupos = ", ".join(f"'{grupo}'" for grupo in GRUPOS_DO_DRE)
    op.execute(f"""
        CREATE TABLE dim.tipo_atividade (
            id    smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            nome  text NOT NULL UNIQUE,
            ordem smallint NOT NULL
        );
        CREATE TABLE dim.atividade_map (
            id                smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            fonte             text NOT NULL CHECK (fonte IN ('planilha', 'metryx', 'manual')),
            nome_origem       text NOT NULL,
            nome_normalizado  text GENERATED ALWAYS AS (app.normalizar(nome_origem)) STORED,
            tipo_atividade_id smallint REFERENCES dim.tipo_atividade(id),    -- NULL = pendente ("A classificar")
            criado_em         timestamptz NOT NULL DEFAULT now(),
            atualizado_em     timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_atividade_map UNIQUE (fonte, nome_normalizado)
        );
        CREATE TABLE dim.classificacao_map (
            id               smallint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
            fonte            text NOT NULL CHECK (fonte IN ('planilha', 'metryx', 'manual')),
            nome_origem      text NOT NULL,
            nome_normalizado text GENERATED ALWAYS AS (app.normalizar(nome_origem)) STORED,
            classificacao    text CHECK (classificacao IN ({grupos})),   -- grupo do DRE; NULL = pendente
            entra_custeio    boolean,
            entra_desembolso boolean,                                    -- a marca da fonte
            criado_em        timestamptz NOT NULL DEFAULT now(),
            atualizado_em    timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_classificacao_map UNIQUE (fonte, nome_normalizado)
        );
        CREATE TABLE dim.conta_bancaria (
            id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            cliente_id    uuid NOT NULL REFERENCES core.cliente(id) ON DELETE CASCADE,
            fonte         text NOT NULL CHECK (fonte IN ('planilha', 'metryx', 'manual')),
            id_externo    text NOT NULL,
            nome          text NOT NULL,
            criado_em     timestamptz NOT NULL DEFAULT now(),
            atualizado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_conta_bancaria UNIQUE (fonte, cliente_id, id_externo)
        );
        COMMENT ON TABLE dim.atividade_map IS 'de-para da atividade da fonte para o tipo de atividade (filtro)';
        COMMENT ON TABLE dim.classificacao_map IS
            'classificação da fonte (Metryx: classificationAnalytic) -> grupo do DRE e marcas de custeio e desembolso';
        COMMENT ON TABLE dim.conta_bancaria IS 'conta bancária dos lançamentos realizados (Metryx), por cliente';
    """)


def semear_as_dimensoes() -> None:
    for ordem, tipo in enumerate(TIPOS_DE_ATIVIDADE, start=1):
        op.execute(f"INSERT INTO dim.tipo_atividade (nome, ordem) VALUES ('{tipo}', {ordem});")
    for atividade, tipo in ATIVIDADES_DO_METRYX.items():
        op.execute(f"""
            INSERT INTO dim.atividade_map (fonte, nome_origem, tipo_atividade_id)
            SELECT 'metryx', '{atividade}', id FROM dim.tipo_atividade WHERE nome = '{tipo}';
        """)
    for nome, (grupo, custeio, desembolso) in CLASSIFICACOES_DO_METRYX.items():
        op.execute(f"""
            INSERT INTO dim.classificacao_map (fonte, nome_origem, classificacao, entra_custeio, entra_desembolso)
            VALUES ('metryx', '{nome}', '{grupo}', {custeio}, {desembolso});
        """)


def downgrade() -> None:
    for tabela in FATOS:
        op.execute(f"DROP VIEW fato.v_{tabela};")
    op.execute("""
        ALTER TABLE fato.lancamento_financeiro
            DROP COLUMN atividade_map_id, DROP COLUMN classificacao_map_id, DROP COLUMN conta_bancaria_id;
        ALTER TABLE fato.orcamento_financeiro DROP COLUMN atividade_map_id, DROP COLUMN classificacao_map_id;
        DROP TABLE dim.conta_bancaria;
        DROP TABLE dim.classificacao_map;
        DROP TABLE dim.atividade_map;
        DROP TABLE dim.tipo_atividade;
    """)
    for tabela in FATOS:
        op.execute(VIEW_ANTERIOR.format(tabela=tabela))
