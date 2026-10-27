"""Tokens Metryx: cifrados no banco (integracao.metryx_credencial), chave Fernet fora do banco (METRYX_CHAVE_CIFRA).

O token só existe em claro na memória do worker durante a extração. Nunca vai para log, repr ou exceção.
"""

import hashlib
from dataclasses import dataclass, field
from uuid import UUID

from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy import Engine, select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.config import get_settings
from app.db.session import sessao
from app.models.core import Cliente, FonteVinculo
from app.models.ingest import MetryxCredencial


class ChaveAusente(RuntimeError):
    pass


def _fernet(chave: str | None = None) -> Fernet:
    chave = chave or get_settings().metryx_chave_cifra
    if not chave:
        raise ChaveAusente("defina METRYX_CHAVE_CIFRA no .env para cifrar/decifrar tokens Metryx")
    return Fernet(chave.encode())


def cifrar(token: str, chave: str | None = None) -> bytes:
    return _fernet(chave).encrypt(token.encode())


def decifrar(cifrado: bytes, chave: str | None = None) -> str:
    try:
        return _fernet(chave).decrypt(bytes(cifrado)).decode()
    except InvalidToken as exc:
        raise ChaveAusente("token não decifra com a METRYX_CHAVE_CIFRA atual") from exc


def impressao(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()[:12]


@dataclass(frozen=True)
class Credencial:
    id: UUID
    cliente_id: UUID
    metryx_customer_id: str
    token: str = field(repr=False)

    def __repr__(self) -> str:   # nunca expor o token
        return f"Credencial(customer={self.metryx_customer_id}, id={self.id})"


def credenciais_ativas(engine: Engine, customers: list[str] | None = None) -> list[Credencial]:
    with sessao(engine) as s:
        q = select(MetryxCredencial).where(MetryxCredencial.status == "ativa")
        if customers:
            q = q.where(MetryxCredencial.metryx_customer_id.in_(customers))
        linhas = s.scalars(q.order_by(MetryxCredencial.criado_em.desc())).all()
    vistos, out = set(), []
    for c in linhas:                       # um token por cliente: o mais recente
        if c.metryx_customer_id in vistos:
            continue
        vistos.add(c.metryx_customer_id)
        out.append(Credencial(c.id, c.cliente_id, c.metryx_customer_id, decifrar(c.token_cifrado)))
    return out


def registrar(engine: Engine, metryx_customer_id: str, token: str, nome_cliente: str) -> UUID:
    """Cadastra (ou rotaciona) o token de um cliente Metryx. Cria o cliente e o vínculo se ainda não existirem."""
    with sessao(engine) as s:
        cliente_id = s.scalar(select(FonteVinculo.entidade_id).where(
            FonteVinculo.fonte == "metryx", FonteVinculo.entidade == "cliente",
            FonteVinculo.id_externo == metryx_customer_id))
        if cliente_id is None:
            cliente_id = s.scalar(pg_insert(Cliente).values(nome=nome_cliente).returning(Cliente.id))
            s.execute(pg_insert(FonteVinculo).values(fonte="metryx", entidade="cliente", id_externo=metryx_customer_id,
                                                     entidade_id=cliente_id, nome_externo=nome_cliente))
        s.execute(update(MetryxCredencial)
                  .where(MetryxCredencial.metryx_customer_id == metryx_customer_id,
                         MetryxCredencial.status == "ativa")
                  .values(status="revogada", atualizado_em=text("now()")))
        stmt = pg_insert(MetryxCredencial).values(
            cliente_id=cliente_id, metryx_customer_id=metryx_customer_id, token_cifrado=cifrar(token),
            token_impressao=impressao(token), status="ativa")
        s.execute(stmt.on_conflict_do_update(constraint="uq_metryx_credencial",
                                             set_={"status": "ativa", "atualizado_em": text("now()")}))
    return cliente_id


def marcar(engine: Engine, credencial_id: UUID, status: str, erro: str | None = None) -> None:
    with sessao(engine) as s:
        s.execute(update(MetryxCredencial).where(MetryxCredencial.id == credencial_id).values(
            status=status, ultimo_erro=erro, ultima_validacao_em=text("now()"), atualizado_em=text("now()")))
