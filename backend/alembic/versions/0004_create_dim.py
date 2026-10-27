"""create_dim: categoria_bi, categoria_map, centro_custo, subcentro, plano_contas_map, calendario, parametro, versao_plano

Seeds idempotentes: 15 categorias BI (aba dCategorias), calendário 2015–2035 (civil + safra jul–jun),
parâmetros e centros de custo unificados (relatório 01 §1.3 + relatório 02 §1.4/§1.6).

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-14
"""

import sqlalchemy as sa
from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

# (id, nome, sexo, grupo, era) — ordem da aba dCategorias (idêntica nos 230 arquivos)
CATEGORIAS_BI = [
    (1, "BEZERRO", "MACHO", "BEZERROS", "00-08"),
    (2, "MACHOS 8-12", "MACHO", "JOVENS", "08-12"),
    (3, "MACHOS 13-24", "MACHO", "JOVENS", "13-24"),
    (4, "MACHOS 25-36", "MACHO", "ADULTOS", "25-36"),
    (5, "MACHOS + 36", "MACHO", "ADULTOS", "+36"),
    (6, "TOUROS", "MACHO", "ADULTOS", "+36"),
    (7, "TOUROS DESCARTES", "MACHO", "ADULTOS", "+36"),
    (8, "SINUELO", "MACHO", "ADULTOS", "+36"),
    (9, "BEZERRA", "FÊMEA", "BEZERROS", "00-08"),
    (10, "NOVILHAS 8-12", "FÊMEA", "JOVENS", "08-12"),
    (11, "NOVILHAS 13-24", "FÊMEA", "JOVENS", "13-24"),
    (12, "NOVILHAS 25-36", "FÊMEA", "ADULTOS", "25-36"),
    (13, "MATRIZES", "FÊMEA", "ADULTOS", "+36"),
    (14, "VACA DESCARTE", "FÊMEA", "ADULTOS", "+36"),
    (15, "VACA LEITEIRA", "FÊMEA", "ADULTOS", "+36"),
]

REC, INV, CUS, OCR, ODB, NEU = (
    "A - RECEITAS", "C - INVESTIMENTOS", "D - CUSTEIO", "E - OUTROS CRÉDITOS", "F - OUTROS DÉBITOS", "NEUTRO",
)
# (nome na taxonomia Metryx, classificação DRE, entra_desembolso (DCM), entra_custeio (CCM), tipo_custeio)
# Flags: CTE `mapa` do BI Metryx. Os marcados com "sem mapa" não estão no `mapa` (lá caem em VERIFICAR) e seguem a
# classificação do P×R por analogia.
# TODO(D3): investimentos fora do custeio (custeio = CCM operacional) — no `mapa` eles entram como CCM.
CENTROS_CUSTO = [
    ("Arrendamento", REC, False, False, "RECEITA_OUTRAS"),
    ("Cultura - Receita", REC, False, False, "RECEITA_AGR"),
    ("Rebanho", REC, False, False, "RECEITA_PEC"),
    ("Receitas financeiras", REC, False, False, "FINANCIAMENTO"),  # assim no `mapa`; conferir
    ("Receitas outros", REC, False, False, "RECEITA_OUTRAS"),
    ("Receitas Parque de máquinas", REC, False, False, "RECEITA_OUTRAS"),
    ("Vendas outros animais", REC, False, False, "RECEITA_OUTRAS"),
    ("Investimentos em infraestrutura", INV, True, False, "CF"),
    ("Investimentos em outros animais", INV, True, False, "CF"),
    ("Investimentos em RH", INV, True, False, None),
    ("Rebanho Investimento", INV, True, False, "CV"),
    ("Algodão", CUS, True, True, "CV"),  # sem mapa
    ("Aveia", CUS, True, True, "CV"),  # sem mapa
    ("Culturas - Despesa", CUS, True, True, "CV"),
    ("Feno", CUS, True, True, "CV"),  # sem mapa
    ("Forrageiras e Culturas Anuais", CUS, True, True, "CV"),
    ("Insumos do rebanho", CUS, True, True, "CV"),
    ("Manutenção da fazenda", CUS, True, True, "CF"),
    ("Mão de Obra Geral", CUS, True, True, "CF"),
    ("Mão de Obra Permanente Administração", CUS, True, True, "CF"),
    ("Mão de Obra Permanente Cultura", CUS, True, True, "CF"),
    ("Mão de Obra Permanente Manutenção da Fazenda", CUS, True, True, "CF"),
    ("Mão de Obra Permanente Parque de Máquinas", CUS, True, True, "CF"),
    ("Mão de Obra Permanente Rebanho", CUS, True, True, "CF"),
    ("Milho Safrinha", CUS, True, True, "CV"),
    ("Milho Verão", CUS, True, True, "CV"),  # sem mapa
    ("Outros animais", CUS, True, True, "CF"),
    ("Pastagens", CUS, True, True, "CV"),
    ("Silagem", CUS, True, True, "CV"),
    ("Silagem de Capiaçu", CUS, True, True, "CV"),  # sem mapa
    ("Silagem de Capim", CUS, True, True, "CV"),
    ("Silagem de Milheto", CUS, True, True, "CV"),
    ("Silagem de Milho", CUS, True, True, "CV"),
    ("Silagem de Sorgo", CUS, True, True, "CV"),  # sem mapa
    ("Soja", CUS, True, True, "CV"),
    ("Sorgo Grão", CUS, True, True, "CV"),
    ("Suporte à Produção Administração", CUS, True, True, "CF"),
    ("Suporte à Produção Parque de máquinas", CUS, True, True, "CF"),
    ("Taxas e impostos", CUS, True, True, "CF"),
    ("Empréstimos sócios crédito", OCR, False, False, None),  # sem mapa
    ("Financiamentos créditos", OCR, False, False, "FINANCIAMENTO"),
    ("Dividendos", ODB, False, False, None),
    ("Empréstimos sócios débito", ODB, False, False, None),
    ("Financiamentos débitos", ODB, True, False, None),  # DCM no `mapa`; conferir com a planilha
    ("Outros Débitos", ODB, False, False, None),  # sem mapa
    ("Almoxarifado", NEU, False, False, None),
    ("Aporte de capital", NEU, False, False, "APORTE"),  # sem mapa
    ("Prejuízo Administração", NEU, False, False, None),  # sem mapa
    ("Venda de Imóveis", NEU, False, False, None),  # sem mapa
    ("Milheto", NEU, False, False, None),  # no `mapa` não entra em nada e não está no CASE do P×R; conferir
]

# (chave, valor numérico, valor texto, descrição)
PARAMETROS = [
    ("kg_carcaca_por_arroba", 15, None, "kg de carcaça por arroba (abate)"),
    ("kg_vivo_por_arroba", 30, None, "kg de peso vivo por arroba (em pé, compra, transferência)"),
    ("kg_por_ua", 450, None, "kg de peso vivo por unidade animal"),
    ("semaforo_limiar", 0.03, None, "limiar do semáforo do Previsto × Realizado"),
    ("multiplicador_gauge_preco", 1.15, None, "máximo do gauge de preço da @ = meta × fator"),
    ("multiplicador_gauge_desembolso", 1.2, None, "máximo do gauge de desembolso/cab/mês = meta × fator"),
    ("cidade_boletim", None, "Cuiabá", "cidade impressa na capa do boletim"),
]


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE dim.categoria_bi (
            id          smallint PRIMARY KEY,
            nome        text NOT NULL UNIQUE,
            sexo        text NOT NULL CHECK (sexo IN ('MACHO','FÊMEA')),
            grupo       text NOT NULL CHECK (grupo IN ('BEZERROS','JOVENS','ADULTOS')),
            era         text NOT NULL CHECK (era IN ('00-08','08-12','13-24','25-36','+36')),
            peso_ref_kg numeric(8,2)            -- TODO(D5): peso de referência p/ UA estimada
        );

        -- De-para categoria da fonte -> categoria BI. Os fatos apontam para esta tabela (não para categoria_bi):
        -- corrigir um mapeamento reclassifica o histórico sem recarga. categoria_bi_id NULL = pendente de confirmação.
        CREATE TABLE dim.categoria_map (
            id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fonte                    text NOT NULL CHECK (fonte IN ('planilha','metryx_realizado','metryx_plano')),
            cliente_id               uuid REFERENCES core.cliente(id) ON DELETE CASCADE,
            fazenda_id               uuid REFERENCES core.fazenda(id) ON DELETE CASCADE,
            categoria_origem         text NOT NULL,   -- chave da categoria na fonte (planilha: nome normalizado; Metryx: id)
            nome_origem              text NOT NULL,
            categoria_bi_id          smallint REFERENCES dim.categoria_bi(id),
            categoria_bi_sugerida_id smallint REFERENCES dim.categoria_bi(id),
            confirmado_por           uuid REFERENCES core.usuario(id),
            confirmado_em            timestamptz,
            atributos                jsonb,
            criado_em                timestamptz NOT NULL DEFAULT now(),
            atualizado_em            timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_categoria_map_escopo CHECK (num_nonnulls(cliente_id, fazenda_id) = 1),
            CONSTRAINT uq_categoria_map UNIQUE NULLS NOT DISTINCT (fonte, cliente_id, fazenda_id, categoria_origem)
        );
        CREATE INDEX ix_categoria_map_fazenda ON dim.categoria_map (fazenda_id);
        CREATE INDEX ix_categoria_map_cliente ON dim.categoria_map (cliente_id);

        CREATE TABLE dim.centro_custo (
            id               smallint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            nome             text NOT NULL UNIQUE,   -- taxonomia Metryx (as planilhas já traduzem para ela)
            nome_normalizado text GENERATED ALWAYS AS (app.normalizar(nome)) STORED UNIQUE,
            classificacao    text NOT NULL CHECK (classificacao IN ('A - RECEITAS','C - INVESTIMENTOS','D - CUSTEIO',
                                                     'E - OUTROS CRÉDITOS','F - OUTROS DÉBITOS','NEUTRO')),
            entra_desembolso boolean NOT NULL,       -- DCM
            entra_custeio    boolean NOT NULL,       -- CCM
            tipo_custeio     text CHECK (tipo_custeio IN ('CF','CV','RECEITA_PEC','RECEITA_AGR','RECEITA_OUTRAS',
                                                          'FINANCIAMENTO','APORTE')),
            eh_reposicao     boolean NOT NULL DEFAULT false,   -- REP.
            ativo            boolean NOT NULL DEFAULT true
        );

        -- Flags NULL = herda do centro de custo (na planilha a classificação é por subconta: ConsultaPlanoContas).
        CREATE TABLE dim.subcentro (
            id               smallint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            centro_custo_id  smallint NOT NULL REFERENCES dim.centro_custo(id),
            nome             text NOT NULL,
            nome_normalizado text GENERATED ALWAYS AS (app.normalizar(nome)) STORED,
            entra_desembolso boolean,
            entra_custeio    boolean,
            tipo_custeio     text CHECK (tipo_custeio IN ('CF','CV','RECEITA_PEC','RECEITA_AGR','RECEITA_OUTRAS',
                                                          'FINANCIAMENTO','APORTE')),
            eh_reposicao     boolean,
            ativo            boolean NOT NULL DEFAULT true,
            CONSTRAINT uq_subcentro UNIQUE (centro_custo_id, nome_normalizado)
        );

        -- De-para (centro, subcentro) da fonte -> plano de contas canônico.
        CREATE TABLE dim.plano_contas_map (
            id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fonte            text NOT NULL CHECK (fonte IN ('planilha','metryx')),
            centro_origem    text NOT NULL,             -- normalizado (app.normalizar)
            subcentro_origem text NOT NULL DEFAULT '',  -- normalizado; '' = qualquer/sem subcentro
            centro_custo_id  smallint NOT NULL REFERENCES dim.centro_custo(id),
            subcentro_id     smallint REFERENCES dim.subcentro(id),
            criado_em        timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_plano_contas_map UNIQUE (fonte, centro_origem, subcentro_origem)
        );

        CREATE TABLE dim.calendario (
            data           date PRIMARY KEY,
            ano            smallint NOT NULL,
            mes            smallint NOT NULL,
            dia            smallint NOT NULL,
            competencia    date NOT NULL,      -- 1º dia do mês
            ultimo_dia_mes date NOT NULL,
            nome_mes       text NOT NULL,      -- 'julho'
            mes_abrev      text NOT NULL,      -- 'jul'
            ano_mes        text NOT NULL,      -- '2025-07'
            rotulo_mes     text NOT NULL,      -- 'jul-25'
            safra_inicio   smallint NOT NULL,  -- safra jul–jun: ano de julho
            safra          text NOT NULL,      -- '2025/26'
            ordem_safra    smallint NOT NULL   -- jul = 1 … jun = 12
        );
        CREATE INDEX ix_calendario_competencia ON dim.calendario (competencia);

        CREATE TABLE dim.parametro (
            chave         text PRIMARY KEY,
            valor         numeric,
            valor_texto   text,
            descricao     text NOT NULL,
            atualizado_em timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT ck_parametro_valor CHECK (num_nonnulls(valor, valor_texto) = 1)
        );

        -- Versões de planejamento. Planilha: uma versão 'PLANILHA' por cliente. Metryx: plVersionCode.
        CREATE TABLE dim.versao_plano (
            id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            cliente_id uuid NOT NULL REFERENCES core.cliente(id) ON DELETE CASCADE,
            fonte      text NOT NULL CHECK (fonte IN ('planilha','metryx','manual')),
            codigo     text NOT NULL,
            nome       text,
            oficial    boolean NOT NULL DEFAULT false,   -- TODO(D7): versão oficial por fazenda/safra
            criado_em  timestamptz NOT NULL DEFAULT now(),
            CONSTRAINT uq_versao_plano UNIQUE (cliente_id, fonte, codigo)
        );
        """
    )

    categoria = sa.table(
        "categoria_bi", sa.column("id"), sa.column("nome"), sa.column("sexo"), sa.column("grupo"), sa.column("era"),
        schema="dim",
    )
    op.bulk_insert(categoria, [dict(zip(("id", "nome", "sexo", "grupo", "era"), c, strict=True)) for c in CATEGORIAS_BI])

    centro = sa.table(
        "centro_custo", sa.column("nome"), sa.column("classificacao"), sa.column("entra_desembolso"),
        sa.column("entra_custeio"), sa.column("tipo_custeio"), schema="dim",
    )
    op.bulk_insert(
        centro,
        [
            dict(zip(("nome", "classificacao", "entra_desembolso", "entra_custeio", "tipo_custeio"), c, strict=True))
            for c in CENTROS_CUSTO
        ],
    )

    parametro = sa.table(
        "parametro", sa.column("chave"), sa.column("valor"), sa.column("valor_texto"), sa.column("descricao"),
        schema="dim",
    )
    op.bulk_insert(
        parametro, [dict(zip(("chave", "valor", "valor_texto", "descricao"), p, strict=True)) for p in PARAMETROS]
    )

    op.execute(
        """
        INSERT INTO dim.calendario
        SELECT d, y, m, extract(day FROM d)::smallint,
               date_trunc('month', d)::date,
               (date_trunc('month', d) + interval '1 month - 1 day')::date,
               (ARRAY['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro',
                      'outubro','novembro','dezembro'])[m],
               (ARRAY['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'])[m],
               to_char(d, 'YYYY-MM'),
               (ARRAY['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez'])[m] || '-' || to_char(d, 'YY'),
               si, si || '/' || lpad(((si + 1) % 100)::text, 2, '0'),
               CASE WHEN m >= 7 THEN m - 6 ELSE m + 6 END
        FROM (
            SELECT d, extract(year FROM d)::smallint AS y, extract(month FROM d)::smallint AS m,
                   (CASE WHEN extract(month FROM d) >= 7 THEN extract(year FROM d)
                         ELSE extract(year FROM d) - 1 END)::smallint AS si
            -- date + inteiro (sem timestamp): imune a fuso/horário de verão
            FROM (SELECT date '2015-01-01' + i AS d
                  FROM generate_series(0, date '2035-12-31' - date '2015-01-01') AS i) dias
        ) s
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE dim.versao_plano;
        DROP TABLE dim.parametro;
        DROP TABLE dim.calendario;
        DROP TABLE dim.plano_contas_map;
        DROP TABLE dim.subcentro;
        DROP TABLE dim.centro_custo;
        DROP TABLE dim.categoria_map;
        DROP TABLE dim.categoria_bi;
        """
    )
