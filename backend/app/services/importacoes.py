"""A tela de importação: recebe a planilha, põe na fila do worker e lista o que já foi enviado.

A API não carrega nada (como no "Atualizar agora"): confere o básico do arquivo (o nome no padrão das planilhas, que é
um arquivo do Excel e o tamanho), guarda em ingest.importacao e avisa o worker. Quem lê a planilha, confere se quem
enviou tem acesso à fazenda dela e carrega é o worker (app/etl/importacao.py). Se a fila não responder, a importação
continua guardada e a agenda do worker a pega depois.
"""

import logging
import unicodedata
from uuid import UUID

from fastapi import HTTPException, status
from kombu.exceptions import OperationalError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.etl.adapters.base import sha256_bytes
from app.etl.adapters.planilha.template import REGEX_ARQUIVO
from app.models.core import Usuario
from app.schemas.importacao import Importacao
from app.tasks.fila import celery

log = logging.getLogger(__name__)

TAREFA = "cargas.importacoes"
TAMANHO_MAXIMO = 50 * 1024 * 1024           # a maior planilha da equipe tem uns 10 MB
COMECO_DO_ZIP = b"PK\x03\x04"               # .xlsm e .xlsx são arquivos zip

NOVA = """
    INSERT INTO ingest.importacao (usuario_id, enviado_por, arquivo, sha256, tamanho_bytes, conteudo)
    VALUES (:usuario, :enviado_por, :arquivo, :sha256, :tamanho, :conteudo)
    RETURNING id
"""
# com o RLS, cada um vê as que enviou e as das fazendas que acompanha; o nome das fazendas, só das que vê
COLUNAS = """
    i.id, i.arquivo, i.tamanho_bytes, i.enviado_por, i.enviado_em,
    coalesce(i.usuario_id = app.usuario_id(), false) AS minha, i.status, i.mensagem, i.avisos, i.quarentena,
    array(SELECT f.nome FROM core.fazenda f WHERE f.id = ANY (i.fazendas) ORDER BY f.nome) AS fazendas,
    i.iniciado_em, i.finalizado_em
"""
RECENTES = f"SELECT {COLUNAS} FROM ingest.importacao i ORDER BY i.enviado_em DESC, i.id LIMIT 100"
UMA = f"SELECT {COLUNAS} FROM ingest.importacao i WHERE i.id = :id"


def receber(s: Session, usuario: Usuario, nome: str | None, dados: bytes) -> Importacao:
    """Guarda a planilha na fila, em nome de quem está logado (o RLS não deixa guardar em nome de outro)."""
    arquivo = nome_conferido(nome)
    conferir_conteudo(arquivo, dados)
    parametros = {"usuario": usuario.id, "enviado_por": usuario.nome, "arquivo": arquivo,
                  "sha256": sha256_bytes(dados), "tamanho": len(dados), "conteudo": dados}
    importacao_id = s.scalar(text(NOVA), parametros)
    return importacao(s, importacao_id)


def nome_conferido(nome: str | None) -> str:
    """O nome segue o padrão das planilhas: o código e a fazenda do nome conferem o fUnidade, e o nome é a chave do
    arquivo na plataforma (enviado de novo com o mesmo nome, vira uma versão nova dele)."""
    arquivo = unicodedata.normalize("NFC", (nome or "").strip())
    if REGEX_ARQUIVO.match(arquivo) is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                            f"'{arquivo}' não segue o padrão do nome das planilhas: "
                            "RELATÓRIO - código do projeto - fazenda.xlsm")
    return arquivo


def conferir_conteudo(arquivo: str, dados: bytes) -> None:
    if len(dados) > TAMANHO_MAXIMO:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, f"{arquivo}: o arquivo passa de 50 MB")
    if not dados.startswith(COMECO_DO_ZIP):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT,
                            f"{arquivo}: não é uma planilha do Excel (.xlsm ou .xlsx)")


def importacao(s: Session, importacao_id: UUID) -> Importacao:
    linha = s.execute(text(UMA), {"id": importacao_id}).mappings().one()
    return Importacao(**linha)


def listar(s: Session) -> list[Importacao]:
    """As 100 mais recentes que o usuário pode ver."""
    linhas = s.execute(text(RECENTES)).mappings()
    return [Importacao(**linha) for linha in linhas]


def avisar_o_worker() -> None:
    """Põe a fila para andar. Sem Redis, a importação fica guardada e a agenda do worker a pega depois."""
    try:
        enviar_para_a_fila()
    except OperationalError as erro:
        log.warning("não deu para avisar o worker da importação (fica para a agenda): %s", erro)


def enviar_para_a_fila() -> None:
    """Pelo nome da tarefa: a API não importa o código das cargas. (Os testes trocam esta função: não há Redis.)"""
    celery.send_task(TAREFA)
