from alembic import command
from sqlalchemy import Engine, inspect, text

from app.db.base import Base
from tests.conftest import alembic_cfg, apagar_banco, criar_banco

SCHEMAS_NEGOCIO = ("core", "dim", "fato", "mart", "ingest", "raw", "integracao", "compat")


def test_migracoes_sobem_e_descem_limpas():
    nome = "terra_test_ciclo"
    criar_banco(nome)
    try:
        cfg = alembic_cfg(nome)
        command.upgrade(cfg, "head")
        command.downgrade(cfg, "base")
        command.upgrade(cfg, "head")
    finally:
        apagar_banco(nome)


def test_seeds(engine_super: Engine):
    with engine_super.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM dim.categoria_bi")) == 15
        assert c.execute(text("SELECT grupo, era FROM dim.categoria_bi WHERE nome = 'NOVILHAS 25-36'")).one() == (
            "ADULTOS", "25-36")
        assert c.scalar(text("SELECT safra FROM dim.calendario WHERE data = '2025-07-01'")) == "2025/26"
        assert c.scalar(text("SELECT safra FROM dim.calendario WHERE data = '2026-06-30'")) == "2025/26"
        assert c.scalar(text("SELECT ordem_safra FROM dim.calendario WHERE data = '2026-01-15'")) == 7
        assert c.scalar(text("SELECT min(data) || '..' || max(data) FROM dim.calendario")) == "2015-01-01..2035-12-31"
        assert c.scalar(text("SELECT valor FROM dim.parametro WHERE chave = 'kg_carcaca_por_arroba'")) == 15
        # TODO(D3): investimentos fora do custeio
        assert c.scalar(text("SELECT bool_or(entra_custeio) FROM dim.centro_custo "
                             "WHERE classificacao = 'C - INVESTIMENTOS'")) is False


def test_toda_tabela_de_negocio_tem_rls_forcado_e_politica(engine_super: Engine):
    with engine_super.connect() as c:
        sem_rls = c.execute(text("""
            SELECT n.nspname || '.' || t.relname
            FROM pg_class t JOIN pg_namespace n ON n.oid = t.relnamespace
            WHERE t.relkind IN ('r','p') AND NOT t.relispartition AND n.nspname = ANY (:s)
              AND (NOT t.relrowsecurity OR NOT t.relforcerowsecurity
                   OR NOT EXISTS (SELECT 1 FROM pg_policy p WHERE p.polrelid = t.oid))
        """), {"s": list(SCHEMAS_NEGOCIO)}).scalars().all()
    assert sem_rls == []


def test_views_de_negocio_usam_security_invoker(engine_super: Engine):
    """View sem security_invoker roda como o dono (app_owner, BYPASSRLS) e furaria o RLS."""
    with engine_super.connect() as c:
        inseguras = c.execute(text("""
            SELECT n.nspname || '.' || v.relname FROM pg_class v JOIN pg_namespace n ON n.oid = v.relnamespace
            WHERE v.relkind = 'v' AND n.nspname = ANY (:s)
              AND NOT coalesce('security_invoker=true' = ANY (v.reloptions), false)
        """), {"s": list(SCHEMAS_NEGOCIO)}).scalars().all()
    assert inseguras == []


def test_papeis_da_aplicacao_nao_ignoram_rls(engine_super: Engine):
    with engine_super.connect() as c:
        papeis = dict(c.execute(text("SELECT rolname, rolsuper OR rolbypassrls FROM pg_roles "
                                     "WHERE rolname IN ('app_user','app_etl')")).all())
    assert papeis == {"app_user": False, "app_etl": False}


def test_models_espelham_o_banco(engine_super: Engine):
    insp = inspect(engine_super)
    divergencias = []
    for tabela in Base.metadata.sorted_tables:
        no_banco = {c["name"] for c in insp.get_columns(tabela.name, schema=tabela.schema)}
        no_model = {c.name for c in tabela.columns}
        if no_banco != no_model:
            divergencias.append((tabela.fullname, sorted(no_banco ^ no_model)))
    assert divergencias == []
