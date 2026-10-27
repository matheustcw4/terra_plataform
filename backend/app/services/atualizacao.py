"""O botão "Atualizar agora" do admin: põe a tarefa `cargas.atualizar_agora` na fila do worker e diz como está a carga
(rodando agora? quando foi a última?).

A API não carrega nada: quem lê as planilhas e o Metryx é o worker, uma carga por vez (trava das cargas). Por isso o
pedido é recusado quando já tem carga rodando, e a tela acompanha pela trava e pelo `ingest.job` mais recente.
"""

import logging
from uuid import UUID

from fastapi import HTTPException, status
from kombu.exceptions import OperationalError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.admin import CargaRecente, PedidoDeAtualizacao, SituacaoDaAtualizacao
from app.tasks.fila import celery
from app.tasks.trava import carga_rodando

log = logging.getLogger(__name__)

TAREFA = "cargas.atualizar_agora"
ULTIMA_CARGA = """
    SELECT fonte, status, iniciado_em, finalizado_em
    FROM ingest.job
    ORDER BY iniciado_em DESC NULLS LAST, criado_em DESC
    LIMIT 1
"""
JA_RODANDO = "já tem uma carga rodando; os dados atualizam quando ela terminar"
FILA_FORA = "a fila das cargas (Redis) não respondeu; confira se o Redis e o worker estão no ar"


def situacao(s: Session) -> SituacaoDaAtualizacao:
    linha = s.execute(text(ULTIMA_CARGA)).mappings().first()
    ultima = None
    if linha is not None:
        ultima = CargaRecente(**linha)
    return SituacaoDaAtualizacao(rodando=carga_rodando(s), agora=s.scalar(text("SELECT now()")), ultima=ultima)


def pedir(s: Session, admin_id: UUID) -> PedidoDeAtualizacao:
    """Põe a atualização na fila. `pedida_em` é o relógio do banco: a carga que começar depois disto é a pedida."""
    if carga_rodando(s):
        raise HTTPException(status.HTTP_409_CONFLICT, JA_RODANDO)
    pedida_em = s.scalar(text("SELECT now()"))
    try:
        enviar_para_a_fila(admin_id)
    except OperationalError as erro:
        log.warning("não deu para pôr a atualização na fila: %s", erro)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, FILA_FORA) from erro
    return PedidoDeAtualizacao(pedida_em=pedida_em)


def enviar_para_a_fila(usuario_id: UUID) -> None:
    """Pelo nome da tarefa: a API não importa o código das cargas. (Os testes trocam esta função: não há Redis.)"""
    celery.send_task(TAREFA, kwargs={"usuario_id": str(usuario_id)})
