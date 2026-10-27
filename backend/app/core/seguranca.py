"""Senha (hash argon2) e token de login (JWT assinado com JWT_SEGREDO)."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app.core.config import get_settings

_hasher = PasswordHasher()


class TokenInvalido(Exception):
    """Token ausente, adulterado ou vencido."""


def hash_da_senha(senha: str) -> str:
    return _hasher.hash(senha)


def senha_confere(senha: str, hash_guardado: str | None) -> bool:
    if not hash_guardado:
        return False
    try:
        return _hasher.verify(hash_guardado, senha)
    except (VerifyMismatchError, InvalidHashError):
        return False


def criar_token(usuario_id: UUID) -> str:
    configuracao = get_settings()
    if len(configuracao.jwt_segredo) < 32:     # chave curta é adivinhável (RFC 7518 §3.2)
        raise RuntimeError("defina JWT_SEGREDO no .env com pelo menos 32 caracteres aleatórios")
    agora = datetime.now(UTC)
    conteudo = {"sub": str(usuario_id), "iat": agora, "exp": agora + timedelta(minutes=configuracao.jwt_minutos)}
    return jwt.encode(conteudo, configuracao.jwt_segredo, algorithm="HS256")


def usuario_do_token(token: str) -> UUID:
    try:
        conteudo = jwt.decode(token, get_settings().jwt_segredo, algorithms=["HS256"])
        return UUID(conteudo["sub"])
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise TokenInvalido(str(exc)) from exc
