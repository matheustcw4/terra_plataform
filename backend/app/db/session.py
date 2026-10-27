"""Engines, sessões e o contexto de RLS.

O contexto do usuário (RLS) é aplicado POR TRANSAÇÃO, num único lugar: o listener `after_begin`
lê `session.info["rls"]` e chama `set_config(..., true)` (local à transação). Nunca `SET` de sessão,
que vazaria pelo pool para a próxima requisição.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Engine, create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@dataclass(frozen=True)
class ContextoRLS:
    usuario_id: UUID


def criar_engine(url: str, **kwargs) -> Engine:
    return create_engine(url, pool_pre_ping=True, **kwargs)


SessionLocal = sessionmaker(autoflush=False, expire_on_commit=False)


@event.listens_for(Session, "after_begin")
def _aplicar_contexto_rls(session: Session, transaction, connection) -> None:
    ctx: ContextoRLS | None = session.info.get("rls")
    # Sempre seta (inclusive vazio): uma transação sem contexto não herda nada.
    connection.execute(
        text("SELECT set_config('app.usuario_id', :u, true)"),
        {"u": str(ctx.usuario_id) if ctx else ""},
    )


_engines: dict[str, Engine] = {}


def engine_api() -> Engine:
    if "api" not in _engines:
        _engines["api"] = criar_engine(get_settings().url_api())
    return _engines["api"]


def engine_etl() -> Engine:
    if "etl" not in _engines:
        _engines["etl"] = criar_engine(get_settings().url_etl())
    return _engines["etl"]


@contextmanager
def sessao(engine: Engine, contexto: ContextoRLS | None = None) -> Iterator[Session]:
    """Sessão com commit no fim e rollback em erro. `contexto` define o usuário visto pelo RLS."""
    s = SessionLocal(bind=engine)
    if contexto is not None:
        s.info["rls"] = contexto
    try:
        yield s
        s.commit()
    except Exception:
        s.rollback()
        raise
    finally:
        s.close()
