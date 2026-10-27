"""Tela de admin de usuários e do acesso de cada um às fazendas (core.usuario_fazenda, N:N).

O cadastro tem nome, e-mail, senha e a função, escolhida no cadastro de funções (core.funcao, services/funcoes.py).

Roda na sessão do admin (o RLS deixa o admin ler e gravar todos os usuários). A senha só entra como hash argon2 e
nunca volta na resposta. O admin não pode tirar o próprio acesso de admin nem se desativar: ficaria sem ninguém para
administrar.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.seguranca import hash_da_senha
from app.schemas.admin import AlteracaoDeUsuario, FazendaDoAcesso, NovoUsuario, UsuarioDoAdmin
from app.services.funcoes import conferir_funcao_ativa

COLUNAS_DO_USUARIO = """
    SELECT u.id, u.nome, u.email, u.funcao_id, f.nome AS funcao, u.eh_admin, u.ativo, u.criado_em,
           (SELECT count(*) FROM core.usuario_fazenda uf WHERE uf.usuario_id = u.id) AS fazendas
    FROM core.usuario u
    LEFT JOIN core.funcao f ON f.id = u.funcao_id
"""
USUARIOS = COLUNAS_DO_USUARIO + " ORDER BY u.nome"
USUARIO = COLUNAS_DO_USUARIO + " WHERE u.id = :id"
CRIAR = """
    INSERT INTO core.usuario (email, nome, senha_hash, funcao_id, eh_admin)
    VALUES (lower(btrim(:email)), btrim(:nome), :hash, :funcao, :admin)
    RETURNING id
"""
# Um comando por campo: só muda o que veio no pedido.
ALTERACOES = {
    "nome": "UPDATE core.usuario SET nome = btrim(:valor), atualizado_em = now() WHERE id = :id",
    "funcao_id": "UPDATE core.usuario SET funcao_id = :valor, atualizado_em = now() WHERE id = :id",
    "eh_admin": "UPDATE core.usuario SET eh_admin = :valor, atualizado_em = now() WHERE id = :id",
    "ativo": "UPDATE core.usuario SET ativo = :valor, atualizado_em = now() WHERE id = :id",
    "senha": "UPDATE core.usuario SET senha_hash = :valor, atualizado_em = now() WHERE id = :id",
}
FAZENDAS = """
    SELECT f.id, f.nome, coalesce(nullif(btrim(f.proprietario), ''), c.nome) AS cliente,
           (SELECT ff.fonte FROM core.fazenda_fonte ff
            WHERE ff.fazenda_id = f.id AND ff.dominio = 'pecuario_realizado') AS origem,
           EXISTS (SELECT 1 FROM core.usuario_fazenda uf
                   WHERE uf.usuario_id = :usuario AND uf.fazenda_id = f.id) AS tem_acesso
    FROM core.fazenda f
    JOIN core.cliente c ON c.id = f.cliente_id
    ORDER BY 3, f.nome
"""
TIRAR_ACESSO = """
    DELETE FROM core.usuario_fazenda
    WHERE usuario_id = :usuario AND NOT (fazenda_id = ANY (CAST(:fazendas AS uuid[])))
"""
DAR_ACESSO = """
    INSERT INTO core.usuario_fazenda (usuario_id, fazenda_id)
    SELECT :usuario, fazenda FROM unnest(CAST(:fazendas AS uuid[])) AS fazenda
    ON CONFLICT DO NOTHING
"""
FAZENDAS_QUE_EXISTEM = "SELECT count(*) FROM core.fazenda WHERE id = ANY (CAST(:fazendas AS uuid[]))"


def listar_usuarios(s: Session) -> list[UsuarioDoAdmin]:
    usuarios = []
    for linha in s.execute(text(USUARIOS)).mappings():
        usuarios.append(UsuarioDoAdmin(**linha))
    return usuarios


def usuario(s: Session, usuario_id: UUID) -> UsuarioDoAdmin:
    linha = s.execute(text(USUARIO), {"id": usuario_id}).mappings().first()
    if linha is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "usuário não encontrado")
    return UsuarioDoAdmin(**linha)


def criar_usuario(s: Session, novo: NovoUsuario) -> UsuarioDoAdmin:
    if "@" not in novo.email:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "e-mail inválido")
    conferir_funcao_ativa(s, novo.funcao_id)
    parametros = {"email": novo.email, "nome": novo.nome, "hash": hash_da_senha(novo.senha),
                  "funcao": novo.funcao_id, "admin": novo.eh_admin}
    try:
        with s.begin_nested():                      # o e-mail repetido desfaz só este INSERT
            usuario_id = s.scalar(text(CRIAR), parametros)
    except IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, "já existe um usuário com este e-mail") from exc
    return usuario(s, usuario_id)


def alterar_usuario(s: Session, usuario_id: UUID, alteracao: AlteracaoDeUsuario, admin_id: UUID) -> UsuarioDoAdmin:
    usuario(s, usuario_id)                          # 404 antes de qualquer mudança
    conferir_que_nao_se_tranca(usuario_id, alteracao, admin_id)
    if alteracao.funcao_id is not None:
        conferir_funcao_ativa(s, alteracao.funcao_id)
    for campo, valor in alteracao.model_dump(exclude_none=True).items():
        valor_gravado = valor
        if campo == "senha":
            valor_gravado = hash_da_senha(valor)
        s.execute(text(ALTERACOES[campo]), {"id": usuario_id, "valor": valor_gravado})
    return usuario(s, usuario_id)


def conferir_que_nao_se_tranca(usuario_id: UUID, alteracao: AlteracaoDeUsuario, admin_id: UUID) -> None:
    if usuario_id != admin_id:
        return
    if alteracao.eh_admin is False or alteracao.ativo is False:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                            "você não pode tirar o seu próprio acesso de admin nem se desativar")


def fazendas_do_usuario(s: Session, usuario_id: UUID) -> list[FazendaDoAcesso]:
    usuario(s, usuario_id)
    fazendas = []
    for linha in s.execute(text(FAZENDAS), {"usuario": usuario_id}).mappings():
        fazendas.append(FazendaDoAcesso(**linha))
    return fazendas


def trocar_acesso(s: Session, usuario_id: UUID, fazendas: list[UUID]) -> list[FazendaDoAcesso]:
    """Deixa o usuário com acesso exatamente às fazendas pedidas."""
    usuario(s, usuario_id)
    ids = [str(fazenda) for fazenda in set(fazendas)]
    if s.scalar(text(FAZENDAS_QUE_EXISTEM), {"fazendas": ids}) != len(ids):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "fazenda inexistente na lista")
    parametros = {"usuario": usuario_id, "fazendas": ids}
    s.execute(text(TIRAR_ACESSO), parametros)
    s.execute(text(DAR_ACESSO), parametros)
    return fazendas_do_usuario(s, usuario_id)
