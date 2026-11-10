"""versao_por_fazenda: a tela escolhe as versões do plano de cada fazenda, ou nenhuma

Com todas as fazendas de um cliente no filtro, valia a versão mais recente de cada uma, e a tela só deixava trocar uma
(pedido do usuário, 10/11/2026). Agora a escolha é por fazenda, de seleção múltipla, e pode ser "nenhum
planejamento":
- fazenda com versões marcadas: entram todas as marcadas, que somam (decisão do usuário: "somar as versões"; um mês
  que duas versões marcadas cobrem conta as duas);
- fazenda marcada "sem planejamento": nada do planejado dela entra (metas, rebanho previsto e orçamento);
- as outras: a mais recente de cada safra, como antes.
`app.versoes_do_planejado` (metas e rebanho previsto) passa a receber as versões marcadas e as fazendas sem
planejamento, e `app.versoes_do_orcamento` faz o mesmo no orçamento de um tipo (no tipo 'previsao', que não tem as
versões do plano, a marcação não muda nada, e o "sem planejamento" tira a previsão da fazenda).

Revision ID: 0025
Revises: 0024
Create Date: 2026-11-10
"""

from alembic import op

revision = "0025"
down_revision = "0024"
branch_labels = None
depends_on = None

# a escolha, igual nas duas funções: `planejado` (fazenda, versão, safra) vem antes, no WITH de cada uma
ESCOLHA = """
   , com_escolha AS (
       SELECT DISTINCT p.fazenda_id FROM planejado p WHERE p.versao_plano_id = ANY (p_versoes)
   )
   SELECT p.fazenda_id, p.safra, p.versao_plano_id
   FROM planejado p
   WHERE p.versao_plano_id = ANY (p_versoes) AND p.fazenda_id <> ALL (coalesce(p_sem_plano, '{}'))
   UNION ALL
   SELECT * FROM (
       SELECT DISTINCT ON (p.fazenda_id, p.safra) p.fazenda_id, p.safra, p.versao_plano_id
       FROM planejado p
       LEFT JOIN dim.versao_plano vp ON vp.id = p.versao_plano_id
       WHERE p.fazenda_id <> ALL (coalesce(p_sem_plano, '{}'))
         AND p.fazenda_id NOT IN (SELECT c.fazenda_id FROM com_escolha c)
       ORDER BY p.fazenda_id, p.safra, vp.ordem DESC NULLS LAST, p.versao_plano_id
   ) mais_recente
"""

FUNCAO_DAS_METAS = f"""
CREATE FUNCTION app.versoes_do_planejado(p_fazendas uuid[], p_versoes uuid[], p_sem_plano uuid[])
RETURNS TABLE (fazenda_id uuid, safra integer, versao_plano_id uuid)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = pg_catalog, pg_temp AS
$$ WITH planejado AS (
       SELECT m.fazenda_id, m.versao_plano_id,
              extract(year FROM m.competencia - interval '6 months')::integer AS safra
       FROM fato.mov_animal m
       WHERE m.cenario = 'planejado' AND m.fazenda_id = ANY (p_fazendas)
       UNION
       SELECT r.fazenda_id, r.versao_plano_id,
              extract(year FROM r.competencia - interval '6 months')::integer
       FROM fato.rebanho_medio_mensal r
       WHERE r.cenario = 'planejado' AND r.fazenda_id = ANY (p_fazendas)
   ){ESCOLHA} $$;
REVOKE ALL ON FUNCTION app.versoes_do_planejado(uuid[], uuid[], uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.versoes_do_planejado(uuid[], uuid[], uuid[]) TO app_user, app_etl;
"""

FUNCAO_DO_ORCAMENTO = f"""
CREATE FUNCTION app.versoes_do_orcamento(p_fazendas uuid[], p_tipo text, p_versoes uuid[], p_sem_plano uuid[])
RETURNS TABLE (fazenda_id uuid, safra integer, versao_plano_id uuid)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = pg_catalog, pg_temp AS
$$ WITH planejado AS (
       SELECT DISTINCT o.fazenda_id, o.versao_plano_id,
              extract(year FROM o.competencia - interval '6 months')::integer AS safra
       FROM fato.orcamento_financeiro o
       WHERE o.tipo = p_tipo AND o.fazenda_id = ANY (p_fazendas)
   ){ESCOLHA} $$;
REVOKE ALL ON FUNCTION app.versoes_do_orcamento(uuid[], text, uuid[], uuid[]) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.versoes_do_orcamento(uuid[], text, uuid[], uuid[]) TO app_user, app_etl;
"""

# a da migração 0019, para o downgrade
FUNCAO_ANTERIOR = """
CREATE FUNCTION app.versoes_do_planejado(p_fazendas uuid[], p_versao uuid)
RETURNS TABLE (fazenda_id uuid, safra integer, versao_plano_id uuid)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = pg_catalog, pg_temp AS
$$ SELECT DISTINCT ON (p.fazenda_id, p.safra) p.fazenda_id, p.safra, p.versao_plano_id
   FROM (
       SELECT m.fazenda_id, m.versao_plano_id,
              extract(year FROM m.competencia - interval '6 months')::integer AS safra
       FROM fato.mov_animal m
       WHERE m.cenario = 'planejado' AND m.fazenda_id = ANY (p_fazendas)
       UNION
       SELECT r.fazenda_id, r.versao_plano_id,
              extract(year FROM r.competencia - interval '6 months')::integer
       FROM fato.rebanho_medio_mensal r
       WHERE r.cenario = 'planejado' AND r.fazenda_id = ANY (p_fazendas)
   ) p
   LEFT JOIN dim.versao_plano vp ON vp.id = p.versao_plano_id
   ORDER BY p.fazenda_id, p.safra, p.versao_plano_id = p_versao DESC NULLS LAST, vp.ordem DESC NULLS LAST,
            p.versao_plano_id $$;
REVOKE ALL ON FUNCTION app.versoes_do_planejado(uuid[], uuid) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION app.versoes_do_planejado(uuid[], uuid) TO app_user, app_etl;
"""


def upgrade() -> None:
    op.execute("DROP FUNCTION app.versoes_do_planejado(uuid[], uuid);")
    op.execute(FUNCAO_DAS_METAS)
    op.execute(FUNCAO_DO_ORCAMENTO)


def downgrade() -> None:
    op.execute("DROP FUNCTION app.versoes_do_orcamento(uuid[], text, uuid[], uuid[]);")
    op.execute("DROP FUNCTION app.versoes_do_planejado(uuid[], uuid[], uuid[]);")
    op.execute(FUNCAO_ANTERIOR)
