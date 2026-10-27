"""Dependências das rotas: o banco da API, quem está logado e a sessão com o RLS desse usuário.

Toda rota de dados recebe `SessaoDoUsuario`: o RLS do banco já deixa ver só as fazendas do usuário (o admin vê
tudo). A rota nunca filtra por permissão sozinha.
"""

from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from app.core.seguranca import TokenInvalido, usuario_do_token
from app.db.session import ContextoRLS, engine_api, sessao
from app.models.core import Usuario

_bearer = HTTPBearer(auto_error=False)


def engine_da_api() -> Engine:
    """Banco que a API usa (app_user, sem BYPASSRLS). Os testes trocam por um banco descartável."""
    return engine_api()


EngineDaApi = Annotated[Engine, Depends(engine_da_api)]


def nao_autenticado(motivo: str) -> HTTPException:
    return HTTPException(status.HTTP_401_UNAUTHORIZED, motivo, headers={"WWW-Authenticate": "Bearer"})


def sessao_do_usuario(engine: EngineDaApi,
                      credenciais: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
                      ) -> Iterator[Session]:
    if credenciais is None:
        raise nao_autenticado("faça login")
    try:
        usuario_id = usuario_do_token(credenciais.credentials)
    except TokenInvalido as exc:
        raise nao_autenticado("sessão expirada ou inválida; faça login de novo") from exc
    with sessao(engine, ContextoRLS(usuario_id)) as s:
        usuario = s.get(Usuario, usuario_id)          # o RLS deixa cada um ler a própria linha
        if usuario is None or not usuario.ativo:
            raise nao_autenticado("usuário inativo ou removido")
        s.info["usuario"] = usuario
        yield s


SessaoDoUsuario = Annotated[Session, Depends(sessao_do_usuario)]


def usuario_logado(s: SessaoDoUsuario) -> Usuario:
    return s.info["usuario"]


UsuarioLogado = Annotated[Usuario, Depends(usuario_logado)]


def admin_logado(usuario: UsuarioLogado) -> Usuario:
    """As telas de administração: só o admin entra (o RLS também só deixa o admin gravar)."""
    if not usuario.eh_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "só o administrador acessa esta área")
    return usuario


AdminLogado = Annotated[Usuario, Depends(admin_logado)]
