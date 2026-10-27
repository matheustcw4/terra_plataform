"""Fixtures de teste com Postgres real (o do docker compose).

Cria um banco descartável `terra_test_<pid>` (dono app_owner), aplica as migrações e conecta com os papéis
reais: `app_etl` para cargas, `app_user` para o que a API veria, superusuário só para preparar/limpar.
"""

import os
import uuid
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text

from app.api.deps import engine_da_api
from app.core.config import RAIZ_REPO, get_settings
from app.db.session import ContextoRLS, sessao
from app.main import app

BANCO_TESTE = f"terra_test_{os.getpid()}"

# tabelas zeradas entre testes (seeds de dimensões ficam)
TABELAS_DADOS = [
    "fato.estoque_mensal", "fato.mov_animal", "fato.inventario", "fato.rebanho_medio_mensal", "fato.area_mensal",
    "fato.lancamento_financeiro", "fato.orcamento_financeiro",
    "ingest.linha_quarentena", "ingest.ocorrencia", "raw.payload", "ingest.unidade_origem", "ingest.versao_origem",
    "ingest.job", "integracao.metryx_credencial",
    "dim.categoria_map", "dim.plano_contas_map", "dim.versao_plano",
    "core.usuario_fazenda", "core.usuario", "core.funcao", "core.fazenda_fonte", "core.fonte_vinculo", "core.retiro",
    "core.fazenda", "core.cliente",
]


def criar_banco(nome: str) -> None:
    adm = create_engine(get_settings().url_migracao("postgres"), isolation_level="AUTOCOMMIT")
    with adm.connect() as c:
        c.execute(text(f'DROP DATABASE IF EXISTS "{nome}" WITH (FORCE)'))
        c.execute(text(f'CREATE DATABASE "{nome}" OWNER app_owner'))
    adm.dispose()


def apagar_banco(nome: str) -> None:
    adm = create_engine(get_settings().url_migracao("postgres"), isolation_level="AUTOCOMMIT")
    with adm.connect() as c:
        c.execute(text(f'DROP DATABASE IF EXISTS "{nome}" WITH (FORCE)'))
    adm.dispose()


def alembic_cfg(banco: str) -> Config:
    cfg = Config(str(RAIZ_REPO / "backend" / "alembic.ini"))
    cfg.set_main_option("script_location", str(RAIZ_REPO / "backend" / "alembic"))
    cfg.attributes["url"] = get_settings().url_migracao(banco)
    return cfg


@pytest.fixture(scope="session")
def banco() -> Iterator[str]:
    criar_banco(BANCO_TESTE)
    command.upgrade(alembic_cfg(BANCO_TESTE), "head")
    yield BANCO_TESTE
    apagar_banco(BANCO_TESTE)


@pytest.fixture(scope="session")
def engine_super(banco: str) -> Iterator[Engine]:
    e = create_engine(get_settings().url_migracao(banco))
    yield e
    e.dispose()


@pytest.fixture(scope="session")
def engine_etl(banco: str) -> Iterator[Engine]:
    e = create_engine(get_settings().url_etl(banco))
    yield e
    e.dispose()


@pytest.fixture(scope="session")
def engine_api(banco: str) -> Iterator[Engine]:
    e = create_engine(get_settings().url_api(banco))
    yield e
    e.dispose()


@pytest.fixture
def api(engine_api, monkeypatch) -> Iterator[TestClient]:
    """A API sobre o banco descartável, conectando como app_user (RLS de verdade)."""
    monkeypatch.setattr(get_settings(), "jwt_segredo", "segredo-so-dos-testes-com-32-caracteres-ou-mais")
    app.dependency_overrides[engine_da_api] = lambda: engine_api
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def limpar(request, engine_super: Engine) -> Iterator[None]:
    yield
    if "sem_limpeza" in request.keywords:
        return
    with engine_super.begin() as c:
        c.execute(text(f"TRUNCATE {', '.join(TABELAS_DADOS)} CASCADE"))


def criar_usuario(engine_super: Engine, email: str, *, admin: bool = False, ativo: bool = True,
                  fazendas: list[uuid.UUID] = ()) -> uuid.UUID:
    with engine_super.begin() as c:
        uid = c.execute(text("INSERT INTO core.usuario (email, nome, eh_admin, ativo) VALUES (:e, :e, :a, :at) "
                             "RETURNING id"), {"e": email, "a": admin, "at": ativo}).scalar_one()
        for f in fazendas:
            c.execute(text("INSERT INTO core.usuario_fazenda (usuario_id, fazenda_id) VALUES (:u, :f)"),
                      {"u": uid, "f": f})
    return uid


def como_usuario(engine_api: Engine, usuario_id: uuid.UUID | None):
    return sessao(engine_api, ContextoRLS(usuario_id) if usuario_id else None)
