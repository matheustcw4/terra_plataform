"""Login (e-mail + senha -> token) e quem está logado."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from app.api.deps import EngineDaApi, UsuarioLogado
from app.core.seguranca import criar_token, hash_da_senha, senha_confere
from app.db.session import sessao
from app.schemas.api import PedidoLogin, RespostaLogin, UsuarioResumo

router = APIRouter(prefix="/auth", tags=["auth"])

# e-mail inexistente também confere uma senha (com um hash qualquer), para o tempo de resposta não revelar quem existe
_HASH_DE_CONTROLE = hash_da_senha("hash-de-controle-para-email-inexistente")


@router.post("/login")
def login(pedido: PedidoLogin, engine: EngineDaApi) -> RespostaLogin:
    with sessao(engine) as s:
        usuario = s.execute(text("SELECT * FROM app.dados_de_login(:email)"), {"email": pedido.email}).first()
    if usuario is None:
        senha_confere(pedido.senha, _HASH_DE_CONTROLE)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "e-mail ou senha incorretos")
    if not usuario.ativo or not senha_confere(pedido.senha, usuario.senha_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "e-mail ou senha incorretos")
    resumo = UsuarioResumo(id=usuario.id, nome=usuario.nome, email=pedido.email.strip().lower(),
                           eh_admin=usuario.eh_admin)
    return RespostaLogin(token=criar_token(usuario.id), usuario=resumo)


@router.get("/me")
def quem_sou(usuario: UsuarioLogado) -> UsuarioResumo:
    return UsuarioResumo(id=usuario.id, nome=usuario.nome, email=usuario.email, eh_admin=usuario.eh_admin)
