"""Telas de administração (só admin): de-paras de categoria e de contas, usuários, funções, acesso às fazendas e o
"Atualizar agora" (põe a carga na fila do worker).

As rotas de escrita gravam (commit) antes de responder: a tela relê a lista logo em seguida.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.deps import AdminLogado, SessaoDoUsuario
from app.schemas.admin import (
    AlteracaoDeFuncao,
    AlteracaoDeUsuario,
    CategoriasDeOrigem,
    ContasDeOrigem,
    FazendaDoAcesso,
    Funcao,
    NovaFuncao,
    NovoUsuario,
    PedidoDeAcesso,
    PedidoDeAtualizacao,
    PedidoDeCategoria,
    PedidoDeConta,
    SituacaoDaAtualizacao,
    UsuarioDoAdmin,
)
from app.services import atualizacao, de_paras, funcoes, usuarios

router = APIRouter(prefix="/admin", tags=["admin"])

Situacao = Annotated[bool, Query(description="true: só os pendentes")]
Busca = Annotated[str, Query(description="parte do nome da categoria/conta, da fazenda ou do cliente")]


@router.get("/categorias")
def listar_categorias(s: SessaoDoUsuario, admin: AdminLogado, so_pendentes: Situacao = True,
                      busca: Busca = "") -> CategoriasDeOrigem:
    return de_paras.listar_categorias(s, so_pendentes, busca)


@router.put("/categorias/{mapa_id}", status_code=204)
def classificar_categoria(s: SessaoDoUsuario, admin: AdminLogado, mapa_id: UUID, pedido: PedidoDeCategoria) -> None:
    de_paras.classificar_categoria(s, mapa_id, pedido.categoria_bi_id, admin.id)
    s.commit()


@router.get("/contas")
def listar_contas(s: SessaoDoUsuario, admin: AdminLogado, so_pendentes: Situacao = True,
                  busca: Busca = "") -> ContasDeOrigem:
    return de_paras.listar_contas(s, so_pendentes, busca)


@router.put("/contas/{mapa_id}", status_code=204)
def classificar_conta(s: SessaoDoUsuario, admin: AdminLogado, mapa_id: UUID, pedido: PedidoDeConta) -> None:
    de_paras.classificar_conta(s, mapa_id, pedido.centro_custo_id, admin.id)
    s.commit()


@router.get("/usuarios")
def listar_usuarios(s: SessaoDoUsuario, admin: AdminLogado) -> list[UsuarioDoAdmin]:
    return usuarios.listar_usuarios(s)


@router.post("/usuarios", status_code=201)
def criar_usuario(s: SessaoDoUsuario, admin: AdminLogado, novo: NovoUsuario) -> UsuarioDoAdmin:
    criado = usuarios.criar_usuario(s, novo)
    s.commit()
    return criado


@router.patch("/usuarios/{usuario_id}")
def alterar_usuario(s: SessaoDoUsuario, admin: AdminLogado, usuario_id: UUID,
                    alteracao: AlteracaoDeUsuario) -> UsuarioDoAdmin:
    alterado = usuarios.alterar_usuario(s, usuario_id, alteracao, admin.id)
    s.commit()
    return alterado


@router.get("/usuarios/{usuario_id}/fazendas")
def fazendas_do_usuario(s: SessaoDoUsuario, admin: AdminLogado, usuario_id: UUID) -> list[FazendaDoAcesso]:
    return usuarios.fazendas_do_usuario(s, usuario_id)


@router.put("/usuarios/{usuario_id}/fazendas")
def trocar_acesso(s: SessaoDoUsuario, admin: AdminLogado, usuario_id: UUID,
                  pedido: PedidoDeAcesso) -> list[FazendaDoAcesso]:
    fazendas = usuarios.trocar_acesso(s, usuario_id, pedido.fazendas)
    s.commit()
    return fazendas


@router.get("/funcoes")
def listar_funcoes(s: SessaoDoUsuario, admin: AdminLogado) -> list[Funcao]:
    return funcoes.listar_funcoes(s)


@router.post("/funcoes", status_code=201)
def criar_funcao(s: SessaoDoUsuario, admin: AdminLogado, nova: NovaFuncao) -> Funcao:
    criada = funcoes.criar_funcao(s, nova.nome)
    s.commit()
    return criada


@router.patch("/funcoes/{funcao_id}")
def alterar_funcao(s: SessaoDoUsuario, admin: AdminLogado, funcao_id: int, alteracao: AlteracaoDeFuncao) -> Funcao:
    alterada = funcoes.alterar_funcao(s, funcao_id, alteracao)
    s.commit()
    return alterada


@router.delete("/funcoes/{funcao_id}", status_code=204)
def apagar_funcao(s: SessaoDoUsuario, admin: AdminLogado, funcao_id: int) -> None:
    funcoes.apagar_funcao(s, funcao_id)
    s.commit()


@router.get("/atualizacao")
def situacao_da_atualizacao(s: SessaoDoUsuario, admin: AdminLogado) -> SituacaoDaAtualizacao:
    return atualizacao.situacao(s)


@router.post("/atualizacao", status_code=202)
def atualizar_agora(s: SessaoDoUsuario, admin: AdminLogado) -> PedidoDeAtualizacao:
    return atualizacao.pedir(s, admin.id)
