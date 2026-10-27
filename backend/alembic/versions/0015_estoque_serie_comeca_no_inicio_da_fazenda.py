"""estoque_serie_comeca_no_inicio_da_fazenda: o movimento que abre uma série nova conta como movimento (A28)

Até a 0010, os fluxos anteriores ao 1º checkpoint de cada série (fazenda × retiro × categoria de origem) eram
ignorados, porque o checkpoint "já os contém". Isso vale para o histórico de antes do saldo inicial da fazenda, mas
erra quando a série nasce do próprio movimento: 7 touros comprados em 07/07 para um retiro que ainda não tinha touro,
com o 1º registro do balanço em 31/07, apareciam como "ajuste" e não como "compra" (relatório de validação §17). Na
planilha, uma categoria do histórico sem saldo anterior perdia meses inteiros de estoque.

Regra nova: o estoque da fazenda começa no PRIMEIRO checkpoint dela (o primeiro retrato). Fluxos até essa data são
ignorados; depois dela, a série que ainda não tem checkpoint começa em zero, e o 1º checkpoint da série corrige o que
não fechar (ajuste). Fazenda sem checkpoint nenhum = soma dos fluxos desde o início, como antes. O resto da 0010 não
muda.

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-15
"""

import importlib.util
from pathlib import Path

from alembic import op

revision = "0015"
down_revision = "0014"
branch_labels = None
depends_on = None

# CREATE OR REPLACE mantém os GRANTs da 0010 (app_etl) e da 0014 (app_user)
FUNCAO = r"""
CREATE OR REPLACE FUNCTION fato.recalcular_estoque_mensal(p_fazendas uuid[], p_ate date DEFAULT current_date)
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    v_linhas integer;
    v_sem_retiro constant uuid := '00000000-0000-0000-0000-000000000000';
BEGIN
    DELETE FROM fato.estoque_mensal e WHERE e.fazenda_id = ANY (p_fazendas) AND e.cenario = 'realizado';

    WITH fluxo AS (
        SELECT m.fazenda_id, coalesce(m.retiro_id, v_sem_retiro) AS retiro, m.categoria_map_id AS chave, m.data,
               CASE m.tipo
                   WHEN 'COMPRA' THEN 'compra'               WHEN 'NASCIMENTO' THEN 'nascimento'
                   WHEN 'TRANSF_ENTRADA' THEN 'transf_entrada' WHEN 'ABATE' THEN 'abate'
                   WHEN 'VENDA_EM_PE' THEN 'venda_em_pe'     WHEN 'MORTE' THEN 'morte'
                   WHEN 'CONSUMO_DOACAO' THEN 'consumo_doacao' WHEN 'TRANSF_SAIDA' THEN 'transf_saida'
                   WHEN 'DESMAME' THEN 'desmame_saida'       WHEN 'MUDANCA_CATEGORIA' THEN 'mudanca_saida'
               END AS coluna,
               CASE WHEN m.tipo IN ('COMPRA','NASCIMENTO','TRANSF_ENTRADA') THEN m.qtd ELSE -m.qtd END AS valor
        FROM fato.mov_animal m
        WHERE m.fazenda_id = ANY (p_fazendas) AND m.cenario = 'realizado'
        UNION ALL
        -- desmame e mudança de categoria: a entrada na categoria de destino
        SELECT m.fazenda_id, coalesce(m.retiro_id, v_sem_retiro), m.categoria_destino_map_id, m.data,
               CASE m.tipo WHEN 'DESMAME' THEN 'desmame_entrada' ELSE 'mudanca_entrada' END,
               m.qtd
        FROM fato.mov_animal m
        WHERE m.fazenda_id = ANY (p_fazendas) AND m.cenario = 'realizado'
          AND m.tipo IN ('DESMAME','MUDANCA_CATEGORIA')
    ),
    evento AS (
        SELECT fazenda_id, retiro, chave, data, 0 AS eh_checkpoint, coluna, valor FROM fluxo
        UNION ALL
        SELECT i.fazenda_id, coalesce(i.retiro_id, v_sem_retiro), i.categoria_map_id, i.data, 1, NULL, sum(i.qtd)
        FROM fato.inventario i
        WHERE i.fazenda_id = ANY (p_fazendas)
        GROUP BY i.fazenda_id, coalesce(i.retiro_id, v_sem_retiro), i.categoria_map_id, i.data
    ),
    inicio_da_fazenda AS (
        -- o primeiro retrato da fazenda: a série que não aparece nele começa em zero
        SELECT i.fazenda_id, min(i.data) AS data
        FROM fato.inventario i
        WHERE i.fazenda_id = ANY (p_fazendas)
        GROUP BY i.fazenda_id
    ),
    ordenado AS (
        -- no mesmo dia, o checkpoint vem depois dos fluxos (ele já os contém)
        SELECT e.*,
               sum(e.eh_checkpoint) OVER w AS trecho,
               row_number() OVER w AS seq
        FROM evento e
        WINDOW w AS (PARTITION BY e.fazenda_id, e.retiro, e.chave ORDER BY e.data, e.eh_checkpoint
                     ROWS UNBOUNDED PRECEDING)
    ),
    corrido AS (
        SELECT o.*,
               sum(o.valor) OVER (PARTITION BY o.fazenda_id, o.retiro, o.chave, o.trecho ORDER BY o.seq
                                  ROWS UNBOUNDED PRECEDING) AS saldo
        FROM ordenado o
        LEFT JOIN inicio_da_fazenda i ON i.fazenda_id = o.fazenda_id
        -- antes do 1º checkpoint da série (trecho 0), o que vem até o início da fazenda já está no retrato dela
        WHERE o.trecho > 0 OR i.data IS NULL OR o.data > i.data
    ),
    fim_mes AS (
        SELECT DISTINCT ON (c.fazenda_id, c.retiro, c.chave, date_trunc('month', c.data))
               c.fazenda_id, c.retiro, c.chave, date_trunc('month', c.data)::date AS competencia, c.saldo
        FROM corrido c
        ORDER BY c.fazenda_id, c.retiro, c.chave, date_trunc('month', c.data), c.seq DESC
    ),
    mov_mes AS (
        SELECT c.fazenda_id, c.retiro, c.chave, date_trunc('month', c.data)::date AS competencia,
               coalesce(sum(c.valor)  FILTER (WHERE c.coluna = 'compra'), 0)          AS compra,
               coalesce(sum(c.valor)  FILTER (WHERE c.coluna = 'nascimento'), 0)      AS nascimento,
               coalesce(sum(c.valor)  FILTER (WHERE c.coluna = 'transf_entrada'), 0)  AS transf_entrada,
               coalesce(sum(c.valor)  FILTER (WHERE c.coluna = 'desmame_entrada'), 0) AS desmame_entrada,
               coalesce(sum(c.valor)  FILTER (WHERE c.coluna = 'mudanca_entrada'), 0) AS mudanca_entrada,
               coalesce(sum(-c.valor) FILTER (WHERE c.coluna = 'abate'), 0)           AS abate,
               coalesce(sum(-c.valor) FILTER (WHERE c.coluna = 'venda_em_pe'), 0)     AS venda_em_pe,
               coalesce(sum(-c.valor) FILTER (WHERE c.coluna = 'morte'), 0)           AS morte,
               coalesce(sum(-c.valor) FILTER (WHERE c.coluna = 'consumo_doacao'), 0)  AS consumo_doacao,
               coalesce(sum(-c.valor) FILTER (WHERE c.coluna = 'transf_saida'), 0)    AS transf_saida,
               coalesce(sum(-c.valor) FILTER (WHERE c.coluna = 'desmame_saida'), 0)   AS desmame_saida,
               coalesce(sum(-c.valor) FILTER (WHERE c.coluna = 'mudanca_saida'), 0)   AS mudanca_saida
        FROM corrido c
        WHERE c.eh_checkpoint = 0
        GROUP BY 1, 2, 3, 4
    ),
    grade AS (
        SELECT l.fazenda_id, l.retiro, l.chave, gs::date AS competencia
        FROM (SELECT fazenda_id, retiro, chave, min(competencia) AS primeiro,
                     greatest(max(competencia), date_trunc('month', p_ate)::date) AS ultimo
              FROM fim_mes GROUP BY 1, 2, 3) l
        CROSS JOIN LATERAL generate_series(l.primeiro, l.ultimo, interval '1 month') AS gs
    ),
    com_evento AS (
        SELECT g.*, f.saldo,
               count(f.saldo) OVER (PARTITION BY g.fazenda_id, g.retiro, g.chave ORDER BY g.competencia) AS bloco
        FROM grade g
        LEFT JOIN fim_mes f USING (fazenda_id, retiro, chave, competencia)
    ),
    saldo_mes AS (
        SELECT fazenda_id, retiro, chave, competencia,
               max(saldo) OVER (PARTITION BY fazenda_id, retiro, chave, bloco) AS saldo_final
        FROM com_evento
    ),
    por_chave AS (
        SELECT s.fazenda_id, s.chave, s.competencia, s.saldo_final,
               coalesce(lag(s.saldo_final) OVER (PARTITION BY s.fazenda_id, s.retiro, s.chave ORDER BY s.competencia),
                        0) AS saldo_inicial,
               coalesce(m.compra, 0) AS compra, coalesce(m.nascimento, 0) AS nascimento,
               coalesce(m.transf_entrada, 0) AS transf_entrada, coalesce(m.desmame_entrada, 0) AS desmame_entrada,
               coalesce(m.mudanca_entrada, 0) AS mudanca_entrada, coalesce(m.abate, 0) AS abate,
               coalesce(m.venda_em_pe, 0) AS venda_em_pe, coalesce(m.morte, 0) AS morte,
               coalesce(m.consumo_doacao, 0) AS consumo_doacao, coalesce(m.transf_saida, 0) AS transf_saida,
               coalesce(m.desmame_saida, 0) AS desmame_saida, coalesce(m.mudanca_saida, 0) AS mudanca_saida
        FROM saldo_mes s
        LEFT JOIN mov_mes m USING (fazenda_id, retiro, chave, competencia)
    )
    INSERT INTO fato.estoque_mensal (
        fazenda_id, cenario, categoria_bi_id, competencia, saldo_inicial,
        compra, nascimento, transf_entrada, desmame_entrada, mudanca_entrada,
        abate, venda_em_pe, morte, consumo_doacao, transf_saida, desmame_saida, mudanca_saida,
        ajuste, saldo_final)
    SELECT p.fazenda_id, 'realizado', cm.categoria_bi_id, p.competencia, sum(p.saldo_inicial),
           sum(p.compra), sum(p.nascimento), sum(p.transf_entrada), sum(p.desmame_entrada), sum(p.mudanca_entrada),
           sum(p.abate), sum(p.venda_em_pe), sum(p.morte), sum(p.consumo_doacao), sum(p.transf_saida),
           sum(p.desmame_saida), sum(p.mudanca_saida),
           sum(p.saldo_final - p.saldo_inicial
               - (p.compra + p.nascimento + p.transf_entrada + p.desmame_entrada + p.mudanca_entrada)
               + (p.abate + p.venda_em_pe + p.morte + p.consumo_doacao + p.transf_saida + p.desmame_saida
                  + p.mudanca_saida)),
           sum(p.saldo_final)
    FROM por_chave p
    JOIN dim.categoria_map cm ON cm.id = p.chave
    WHERE cm.categoria_bi_id IS NOT NULL
    GROUP BY p.fazenda_id, cm.categoria_bi_id, p.competencia;

    GET DIAGNOSTICS v_linhas = ROW_COUNT;
    RETURN v_linhas;
END
$$;
"""


def funcao_da_0010() -> str:
    """O texto da função na 0010, para o downgrade voltar à regra anterior sem copiar a função inteira aqui."""
    caminho = Path(__file__).with_name("0010_funcao_estoque_mensal.py")
    especificacao = importlib.util.spec_from_file_location("migracao_0010", caminho)
    modulo = importlib.util.module_from_spec(especificacao)
    especificacao.loader.exec_module(modulo)
    return modulo.FUNCAO


def upgrade() -> None:
    op.execute(FUNCAO)


def downgrade() -> None:
    op.execute(funcao_da_0010().replace("CREATE FUNCTION", "CREATE OR REPLACE FUNCTION", 1))
