"""create_fato: mov_animal, inventario, rebanho_medio_mensal, area_mensal, lancamento_financeiro,
orcamento_financeiro, estoque_mensal

O canônico guarda grandezas físicas e totais (cab, kg vivo total, kg carcaça total, R$ total, ha, datas).
Médias, preços, arrobas, % e UA são calculados na camada de KPI.

Revision ID: 0008
Revises: 0007
Create Date: 2026-10-14
"""

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None

# colunas técnicas comuns a todos os fatos carregados por adapter
TECNICAS = """
            fonte          text NOT NULL CHECK (fonte IN ('planilha','metryx','manual')),
            origem_ref     uuid NOT NULL REFERENCES ingest.versao_origem(id),
            origem_linha   text NOT NULL,          -- aba!linha (planilha) ou hash#ocorrência (Metryx)
            extra          jsonb,                  -- campos da origem não mapeados: nada se perde
            ingest_job_id  uuid,
            carregado_em   timestamptz NOT NULL DEFAULT now()
"""

COMPETENCIA_1O_DIA = "CHECK (extract(day FROM competencia) = 1)"


def upgrade() -> None:
    op.execute(
        f"""
        CREATE TABLE fato.mov_animal (
            id                       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fazenda_id               uuid NOT NULL REFERENCES core.fazenda(id),
            retiro_id                uuid REFERENCES core.retiro(id),
            cenario                  text NOT NULL CHECK (cenario IN ('realizado','planejado')),
            versao_plano_id          uuid REFERENCES dim.versao_plano(id),
            tipo                     text NOT NULL CHECK (tipo IN ('COMPRA','NASCIMENTO','TRANSF_ENTRADA','ABATE',
                                         'VENDA_EM_PE','MORTE','CONSUMO_DOACAO','TRANSF_SAIDA','DESMAME',
                                         'MUDANCA_CATEGORIA')),
            data                     date NOT NULL,
            competencia              date GENERATED ALWAYS AS (date_trunc('month', data::timestamp)::date) STORED,
            categoria_map_id         uuid NOT NULL REFERENCES dim.categoria_map(id),
            categoria_destino_map_id uuid REFERENCES dim.categoria_map(id),   -- desmame / mudança de categoria
            qtd                      numeric(14,3) NOT NULL CHECK (qtd >= 0),
            peso_vivo_total_kg       numeric(16,3) CHECK (peso_vivo_total_kg >= 0),
            peso_carcaca_total_kg    numeric(16,3) CHECK (peso_carcaca_total_kg >= 0),
            valor_total              numeric(16,2) CHECK (valor_total >= 0),
            contraparte              text,         -- frigorífico / comprador / fornecedor / destino
            documento                text,
            causa                    text,
            local                    text,
            era                      text,
            safra                    text,
            {TECNICAS},
            CONSTRAINT ck_mov_animal_versao CHECK ((cenario = 'realizado') = (versao_plano_id IS NULL)),
            CONSTRAINT ck_mov_animal_destino
                CHECK ((tipo IN ('DESMAME','MUDANCA_CATEGORIA')) = (categoria_destino_map_id IS NOT NULL))
        );
        CREATE INDEX ix_mov_animal_consulta ON fato.mov_animal (fazenda_id, cenario, tipo, data);
        CREATE INDEX ix_mov_animal_categoria ON fato.mov_animal (categoria_map_id);
        CREATE INDEX ix_mov_animal_categoria_destino ON fato.mov_animal (categoria_destino_map_id)
            WHERE categoria_destino_map_id IS NOT NULL;
        CREATE INDEX ix_mov_animal_origem ON fato.mov_animal (origem_ref);

        -- Checkpoints de estoque (saldo informado numa data): saldo inicial da planilha, balanço/saldo inicial Metryx.
        CREATE TABLE fato.inventario (
            id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fazenda_id       uuid NOT NULL REFERENCES core.fazenda(id),
            retiro_id        uuid REFERENCES core.retiro(id),
            categoria_map_id uuid NOT NULL REFERENCES dim.categoria_map(id),
            data             date NOT NULL,      -- saldo ao FIM deste dia
            qtd              numeric(14,3) NOT NULL CHECK (qtd >= 0),
            {TECNICAS},
            CONSTRAINT uq_inventario UNIQUE NULLS NOT DISTINCT (fazenda_id, retiro_id, categoria_map_id, data)
        );
        CREATE INDEX ix_inventario_origem ON fato.inventario (origem_ref);

        -- Grão mínimo comum: grupo × mês. Planilha informa o grupo; Metryx informa a categoria (grupo vem da dimensão).
        CREATE TABLE fato.rebanho_medio_mensal (
            id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fazenda_id         uuid NOT NULL REFERENCES core.fazenda(id),
            cenario            text NOT NULL CHECK (cenario IN ('realizado','planejado')),
            versao_plano_id    uuid REFERENCES dim.versao_plano(id),
            competencia        date NOT NULL {COMPETENCIA_1O_DIA},
            grupo              text CHECK (grupo IN ('BEZERROS','JOVENS','ADULTOS')),
            categoria_map_id   uuid REFERENCES dim.categoria_map(id),
            qtd_cab            numeric(14,3) NOT NULL CHECK (qtd_cab >= 0),
            peso_vivo_total_kg numeric(16,3) CHECK (peso_vivo_total_kg >= 0),
            qtd_ua_informada   numeric(14,3) CHECK (qtd_ua_informada >= 0),
            {TECNICAS},
            CONSTRAINT ck_rebanho_medio_versao CHECK ((cenario = 'realizado') = (versao_plano_id IS NULL)),
            CONSTRAINT ck_rebanho_medio_grao CHECK (num_nonnulls(grupo, categoria_map_id) = 1),
            CONSTRAINT uq_rebanho_medio UNIQUE NULLS NOT DISTINCT
                (fazenda_id, cenario, versao_plano_id, competencia, grupo, categoria_map_id)
        );
        CREATE INDEX ix_rebanho_medio_origem ON fato.rebanho_medio_mensal (origem_ref);

        CREATE TABLE fato.area_mensal (
            id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fazenda_id        uuid NOT NULL REFERENCES core.fazenda(id),
            cenario           text NOT NULL CHECK (cenario IN ('realizado','planejado')),
            versao_plano_id   uuid REFERENCES dim.versao_plano(id),
            competencia       date NOT NULL {COMPETENCIA_1O_DIA},
            area_pasto_ha     numeric(12,3) CHECK (area_pasto_ha >= 0),
            area_ilp_ha       numeric(12,3) CHECK (area_ilp_ha >= 0),
            area_total_ha     numeric(12,3) CHECK (area_total_ha >= 0),
            area_produtiva_ha numeric(12,3) CHECK (area_produtiva_ha >= 0),
            {TECNICAS},
            CONSTRAINT ck_area_versao CHECK ((cenario = 'realizado') = (versao_plano_id IS NULL)),
            CONSTRAINT uq_area_mensal UNIQUE NULLS NOT DISTINCT (fazenda_id, cenario, versao_plano_id, competencia)
        );
        CREATE INDEX ix_area_origem ON fato.area_mensal (origem_ref);

        CREATE TABLE fato.lancamento_financeiro (
            id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fazenda_id        uuid NOT NULL REFERENCES core.fazenda(id),
            fazenda_fiscal_id uuid REFERENCES core.fazenda(id),
            centro_custo_id   smallint NOT NULL REFERENCES dim.centro_custo(id),
            subcentro_id      smallint REFERENCES dim.subcentro(id),
            natureza          char(1) NOT NULL CHECK (natureza IN ('C','D')),
            valor             numeric(16,2) NOT NULL CHECK (valor >= 0),
            data_pagamento    date NOT NULL,
            data_vencimento   date,
            -- TODO(D2): competência pela data de pagamento (fluxo de caixa, igual à planilha)
            competencia       date GENERATED ALWAYS AS (date_trunc('month', data_pagamento::timestamp)::date) STORED,
            descricao         text,
            contraparte       text,
            documento         text,
            {TECNICAS}
        );
        CREATE INDEX ix_lancamento_consulta ON fato.lancamento_financeiro (fazenda_id, competencia);
        CREATE INDEX ix_lancamento_centro ON fato.lancamento_financeiro (centro_custo_id);
        CREATE INDEX ix_lancamento_origem ON fato.lancamento_financeiro (origem_ref);

        CREATE TABLE fato.orcamento_financeiro (
            id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            fazenda_id      uuid NOT NULL REFERENCES core.fazenda(id),
            versao_plano_id uuid NOT NULL REFERENCES dim.versao_plano(id),
            centro_custo_id smallint NOT NULL REFERENCES dim.centro_custo(id),
            subcentro_id    smallint REFERENCES dim.subcentro(id),
            natureza        char(1) NOT NULL CHECK (natureza IN ('C','D')),
            competencia     date NOT NULL {COMPETENCIA_1O_DIA},
            valor           numeric(16,2) NOT NULL CHECK (valor >= 0),
            {TECNICAS}
        );
        CREATE INDEX ix_orcamento_consulta ON fato.orcamento_financeiro (fazenda_id, versao_plano_id, competencia);
        CREATE INDEX ix_orcamento_origem ON fato.orcamento_financeiro (origem_ref);

        -- Derivado (fato.recalcular_estoque_mensal): balanço de rebanho por fazenda × categoria BI × mês.
        -- Saídas em quantidade positiva. A identidade do balanço é garantida por CHECK.
        CREATE TABLE fato.estoque_mensal (
            fazenda_id      uuid NOT NULL REFERENCES core.fazenda(id) ON DELETE CASCADE,
            cenario         text NOT NULL CHECK (cenario IN ('realizado','planejado')),
            categoria_bi_id smallint NOT NULL REFERENCES dim.categoria_bi(id),
            competencia     date NOT NULL {COMPETENCIA_1O_DIA},
            saldo_inicial   numeric(14,3) NOT NULL,
            compra          numeric(14,3) NOT NULL DEFAULT 0,
            nascimento      numeric(14,3) NOT NULL DEFAULT 0,
            transf_entrada  numeric(14,3) NOT NULL DEFAULT 0,
            desmame_entrada numeric(14,3) NOT NULL DEFAULT 0,
            mudanca_entrada numeric(14,3) NOT NULL DEFAULT 0,
            abate           numeric(14,3) NOT NULL DEFAULT 0,
            venda_em_pe     numeric(14,3) NOT NULL DEFAULT 0,
            morte           numeric(14,3) NOT NULL DEFAULT 0,
            consumo_doacao  numeric(14,3) NOT NULL DEFAULT 0,
            transf_saida    numeric(14,3) NOT NULL DEFAULT 0,
            desmame_saida   numeric(14,3) NOT NULL DEFAULT 0,
            mudanca_saida   numeric(14,3) NOT NULL DEFAULT 0,
            ajuste          numeric(14,3) NOT NULL DEFAULT 0,   -- ajuste de inventário (checkpoint × fluxos)
            saldo_final     numeric(14,3) NOT NULL,
            calculado_em    timestamptz NOT NULL DEFAULT now(),
            PRIMARY KEY (fazenda_id, cenario, categoria_bi_id, competencia),
            CONSTRAINT ck_estoque_identidade CHECK (
                saldo_final = saldo_inicial
                    + compra + nascimento + transf_entrada + desmame_entrada + mudanca_entrada
                    - abate - venda_em_pe - morte - consumo_doacao - transf_saida - desmame_saida - mudanca_saida
                    + ajuste)
        );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP TABLE fato.estoque_mensal;
        DROP TABLE fato.orcamento_financeiro;
        DROP TABLE fato.lancamento_financeiro;
        DROP TABLE fato.area_mensal;
        DROP TABLE fato.rebanho_medio_mensal;
        DROP TABLE fato.inventario;
        DROP TABLE fato.mov_animal;
        """
    )
