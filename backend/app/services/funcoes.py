"""Cadastro de funções (core.funcao): a lista de onde sai a função de cada usuário, editada só pelo admin.

O nome é único sem diferenciar maiúsculas ("Consultor" = "consultor"). Função que algum usuário tem não se apaga:
desativa-se, e ela some da lista dos cadastros novos (quem já a tem continua com ela).
"""

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.schemas.admin import AlteracaoDeFuncao, Funcao

FUNCOES = """
    SELECT f.id, f.nome, f.ativo, (SELECT count(*) FROM core.usuario u WHERE u.funcao_id = f.id) AS usuarios
    FROM core.funcao f
    ORDER BY f.ativo DESC, f.nome
"""
FUNCAO = """
    SELECT f.id, f.nome, f.ativo, (SELECT count(*) FROM core.usuario u WHERE u.funcao_id = f.id) AS usuarios
    FROM core.funcao f
    WHERE f.id = :id
"""
CRIAR = "INSERT INTO core.funcao (nome) VALUES (btrim(:nome)) RETURNING id"
ALTERACOES = {
    "nome": "UPDATE core.funcao SET nome = btrim(:valor), atualizado_em = now() WHERE id = :id",
    "ativo": "UPDATE core.funcao SET ativo = :valor, atualizado_em = now() WHERE id = :id",
}
APAGAR = "DELETE FROM core.funcao WHERE id = :id"
ATIVA = "SELECT ativo FROM core.funcao WHERE id = :id"
NOME_REPETIDO = "já existe uma função com este nome"


def listar_funcoes(s: Session) -> list[Funcao]:
    funcoes = []
    for linha in s.execute(text(FUNCOES)).mappings():
        funcoes.append(Funcao(**linha))
    return funcoes


def funcao(s: Session, funcao_id: int) -> Funcao:
    linha = s.execute(text(FUNCAO), {"id": funcao_id}).mappings().first()
    if linha is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "função não encontrada")
    return Funcao(**linha)


def criar_funcao(s: Session, nome: str) -> Funcao:
    conferir_nome(nome)
    try:
        with s.begin_nested():                      # o nome repetido desfaz só este INSERT
            funcao_id = s.scalar(text(CRIAR), {"nome": nome})
    except IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, NOME_REPETIDO) from exc
    return funcao(s, funcao_id)


def alterar_funcao(s: Session, funcao_id: int, alteracao: AlteracaoDeFuncao) -> Funcao:
    funcao(s, funcao_id)                            # 404 antes de qualquer mudança
    if alteracao.nome is not None:
        conferir_nome(alteracao.nome)
    try:
        with s.begin_nested():
            for campo, valor in alteracao.model_dump(exclude_none=True).items():
                s.execute(text(ALTERACOES[campo]), {"id": funcao_id, "valor": valor})
    except IntegrityError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, NOME_REPETIDO) from exc
    return funcao(s, funcao_id)


def apagar_funcao(s: Session, funcao_id: int) -> None:
    if funcao(s, funcao_id).usuarios > 0:
        raise HTTPException(status.HTTP_409_CONFLICT,
                            "há usuários com esta função: desative-a em vez de apagar")
    s.execute(text(APAGAR), {"id": funcao_id})


def conferir_nome(nome: str) -> None:
    if nome.strip() == "":
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "o nome da função não pode ficar em branco")


def conferir_funcao_ativa(s: Session, funcao_id: int) -> None:
    """A função escolhida no cadastro do usuário tem de existir e estar ativa."""
    if s.scalar(text(ATIVA), {"id": funcao_id}) is not True:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "função inexistente ou inativa")
