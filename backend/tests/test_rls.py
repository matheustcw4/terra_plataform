"""Isolamento por usuário: conectado como app_user, cada usuário só lê as fazendas que lhe foram concedidas,
e só admin grava. Os dados são carregados pelo motor real (app_etl)."""

from datetime import date
from uuid import UUID

import pytest
from sqlalchemy import Engine, text
from sqlalchemy.exc import ProgrammingError

from app.etl.pipeline import MotorCarga
from tests.conftest import como_usuario, criar_usuario
from tests.fabrica import AdapterMemoria, exemplo_doc01

TABELAS_POR_FAZENDA = {
    "core.fazenda": "id", "core.fazenda_fonte": "fazenda_id", "fato.mov_animal": "fazenda_id",
    "fato.inventario": "fazenda_id", "fato.estoque_mensal": "fazenda_id", "ingest.ocorrencia": "fazenda_id",
}


@pytest.fixture
def duas_fazendas(engine_etl: Engine, engine_super: Engine) -> dict[str, UUID]:
    lotes = {
        "A": exemplo_doc01(cliente="1", fazenda="1|ALFA", nome_fazenda="ALFA"),
        "B": exemplo_doc01(cliente="2", fazenda="2|BETA", nome_fazenda="BETA"),
    }
    MotorCarga(engine_etl, hoje=date(2025, 10, 1), estoque_ate=date(2025, 9, 1)).executar(
        AdapterMemoria("planilha", lotes))
    with engine_super.connect() as c:
        return dict(c.execute(text("SELECT nome_externo, entidade_id FROM core.fonte_vinculo "
                                   "WHERE entidade = 'fazenda'")).all())


def _fazendas_visiveis(engine_api: Engine, usuario: UUID | None) -> dict[str, set]:
    with como_usuario(engine_api, usuario) as s:
        return {t: set(s.execute(text(f"SELECT DISTINCT {col} FROM {t}")).scalars())
                for t, col in TABELAS_POR_FAZENDA.items()}


def test_usuario_ve_so_as_suas_fazendas(duas_fazendas, engine_api, engine_super):
    a, b = duas_fazendas["ALFA"], duas_fazendas["BETA"]
    ua = criar_usuario(engine_super, "a@x.com", fazendas=[a])
    ub = criar_usuario(engine_super, "b@x.com", fazendas=[b])
    uab = criar_usuario(engine_super, "ab@x.com", fazendas=[a, b])   # mais de um usuário vendo a mesma fazenda

    vistos_a = _fazendas_visiveis(engine_api, ua)
    assert all(v == {a} for v in vistos_a.values()), vistos_a
    assert all(v == {b} for v in _fazendas_visiveis(engine_api, ub).values())
    assert all(v == {a, b} for v in _fazendas_visiveis(engine_api, uab).values())

    with como_usuario(engine_api, ua) as s:
        assert s.execute(text("SELECT count(*) FROM fato.mov_animal")).scalar() == 3
        assert set(s.execute(text("SELECT nome FROM core.cliente")).scalars()) == {"CLIENTE 1"}
        assert s.execute(text("SELECT count(*) FROM dim.categoria_map")).scalar() == 2
        assert s.execute(text("SELECT count(*) FROM core.usuario")).scalar() == 1     # só ele mesmo
        assert s.execute(text("SELECT count(*) FROM ingest.versao_origem")).scalar() == 0  # só admin/ETL


def test_sem_contexto_ou_inativo_nao_ve_nada(duas_fazendas, engine_api, engine_super):
    inativo = criar_usuario(engine_super, "x@x.com", ativo=False, fazendas=[duas_fazendas["ALFA"]])
    for usuario in (None, inativo):
        assert all(v == set() for v in _fazendas_visiveis(engine_api, usuario).values())


def test_usuario_comum_nao_grava(duas_fazendas, engine_api, engine_super):
    a, b = duas_fazendas["ALFA"], duas_fazendas["BETA"]
    ua = criar_usuario(engine_super, "a@x.com", fazendas=[a])
    with como_usuario(engine_api, ua) as s:
        assert s.execute(text("UPDATE fato.mov_animal SET qtd = 0")).rowcount == 0
        assert s.execute(text("DELETE FROM fato.mov_animal")).rowcount == 0
        assert s.execute(text("UPDATE core.fazenda SET nome = 'X'")).rowcount == 0
    for fazenda in (a, b):
        with pytest.raises(ProgrammingError, match="row-level security"), como_usuario(engine_api, ua) as s:
            s.execute(text("INSERT INTO core.retiro (fazenda_id, nome) VALUES (:f, 'R')"), {"f": fazenda})
    with engine_super.connect() as c:
        assert c.execute(text("SELECT count(*) FROM fato.mov_animal WHERE qtd = 0")).scalar() == 0


def test_admin_ve_e_grava_tudo(duas_fazendas, engine_api, engine_super):
    adm = criar_usuario(engine_super, "adm@x.com", admin=True)
    assert all(v == set(duas_fazendas.values()) for v in _fazendas_visiveis(engine_api, adm).values())
    with como_usuario(engine_api, adm) as s:
        s.execute(text("INSERT INTO core.retiro (fazenda_id, nome) VALUES (:f, 'R2')"), {"f": duas_fazendas["BETA"]})
        assert s.execute(text("UPDATE core.fazenda SET nome = nome")).rowcount == 2


def test_contexto_nao_vaza_entre_transacoes(duas_fazendas, engine_api, engine_super):
    """O contexto é local à transação: a conexão devolvida ao pool não carrega o usuário anterior."""
    adm = criar_usuario(engine_super, "adm@x.com", admin=True)
    with como_usuario(engine_api, adm) as s:
        assert s.execute(text("SELECT count(*) FROM core.fazenda")).scalar() == 2
    with engine_api.connect() as c:   # mesma pool, sem contexto
        assert c.execute(text("SELECT count(*) FROM core.fazenda")).scalar() == 0
        assert c.execute(text("SELECT current_setting('app.usuario_id', true)")).scalar() in (None, "")


def test_token_metryx_nao_e_legivel_pela_api(engine_api, engine_super):
    adm = criar_usuario(engine_super, "adm@x.com", admin=True)
    with engine_super.begin() as c:
        cliente = c.execute(text("INSERT INTO core.cliente (nome) VALUES ('C') RETURNING id")).scalar()
    with como_usuario(engine_api, adm) as s:   # admin cadastra (campo write-only)…
        s.execute(text("INSERT INTO integracao.metryx_credencial (cliente_id, metryx_customer_id, token_cifrado, "
                       "token_impressao) VALUES (:c, '99', 'xx', 'abc')"), {"c": cliente})
    with pytest.raises(ProgrammingError, match="permission denied"), como_usuario(engine_api, adm) as s:
        s.execute(text("SELECT token_cifrado FROM integracao.metryx_credencial"))   # …mas não lê


def test_views_do_financeiro_respeitam_o_rls(engine_etl, engine_api, engine_super):
    from decimal import Decimal

    from app.etl.canonical import ContaOrigem, LancamentoFinanceiro, Particao
    from tests.fabrica import lote_base

    lotes = {}
    for cod, nome in (("1", "ALFA"), ("2", "BETA")):
        lote = lote_base(cliente=cod, fazenda=f"{cod}|{nome}", nome_fazenda=nome)
        lote.lancamentos = [LancamentoFinanceiro(fazenda=f"{cod}|{nome}", conta=ContaOrigem(centro="Conta X"),
                                                 natureza="D", valor=Decimal(10), data_pagamento=date(2025, 8, 1),
                                                 origem_linha="fDre!2")]
        lote.particoes = [Particao(entidade="lancamento", fazenda=f"{cod}|{nome}", cenario="realizado",
                                   estrategia="substituir")]
        lotes[nome] = lote
    MotorCarga(engine_etl, hoje=date(2025, 10, 1)).executar(AdapterMemoria("planilha", lotes))
    with engine_super.connect() as c:
        alfa = c.execute(text("SELECT entidade_id FROM core.fonte_vinculo WHERE id_externo = '1|ALFA'")).scalar()
    ua = criar_usuario(engine_super, "a@x.com", fazendas=[alfa])
    with como_usuario(engine_api, ua) as s:
        assert set(s.execute(text("SELECT fazenda_id FROM fato.v_lancamento_financeiro")).scalars()) == {alfa}
    with como_usuario(engine_api, None) as s:
        assert s.execute(text("SELECT count(*) FROM fato.v_lancamento_financeiro")).scalar() == 0


def test_funcao_e_lida_por_todos_e_gravada_so_pelo_admin(engine_api, engine_super):
    with engine_super.begin() as c:
        c.execute(text("INSERT INTO core.funcao (nome) VALUES ('Consultor')"))
    comum = criar_usuario(engine_super, "comum@x.com")
    with como_usuario(engine_api, comum) as s:
        assert s.execute(text("SELECT nome FROM core.funcao")).scalars().all() == ["Consultor"]
        assert s.execute(text("UPDATE core.funcao SET nome = 'X'")).rowcount == 0
        assert s.execute(text("DELETE FROM core.funcao")).rowcount == 0
    with pytest.raises(ProgrammingError, match="row-level security"), como_usuario(engine_api, comum) as s:
        s.execute(text("INSERT INTO core.funcao (nome) VALUES ('Intrusa')"))
    adm = criar_usuario(engine_super, "adm@x.com", admin=True)
    with como_usuario(engine_api, adm) as s:
        s.execute(text("INSERT INTO core.funcao (nome) VALUES ('Gerente')"))
        assert s.execute(text("UPDATE core.funcao SET ativo = ativo")).rowcount == 2
