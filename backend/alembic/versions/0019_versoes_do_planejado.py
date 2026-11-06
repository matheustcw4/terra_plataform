"""versoes_do_planejado

As metas de animais e o rebanho médio previsto passam a guardar todas as versões do plano (pedido do usuário,
04/11/2026), e as telas escolhem a versão. Esta função diz qual versão vale em cada fazenda e safra (jul a jun): a
pedida, se ela tem planejado ali; senão, a mais recente (maior `dim.versao_plano.ordem`). Os KPIs filtram o planejado
por ela (`app/kpis/versao_do_plano.py`).

SECURITY INVOKER: roda sob o RLS de quem consulta (a API como app_user só vê as fazendas do usuário).

Revision ID: 0019
Revises: 0018
Create Date: 2026-11-04
"""

from alembic import op

revision = "0019"
down_revision = "0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
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
        CREATE INDEX ix_mov_animal_planejado ON fato.mov_animal (fazenda_id, versao_plano_id)
            WHERE cenario = 'planejado';
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX fato.ix_mov_animal_planejado;
        DROP FUNCTION app.versoes_do_planejado(uuid[], uuid);
        """
    )
