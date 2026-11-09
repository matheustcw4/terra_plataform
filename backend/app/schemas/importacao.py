"""Formato da tela de importação de planilhas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

SituacaoDaImportacao = Literal["na_fila", "processando", "carregada", "carregada_com_avisos", "inalterada",
                               "ignorada", "erro"]


class Importacao(BaseModel):
    """Uma planilha enviada pela tela: espera o worker na fila e, depois, mostra o que a carga fez."""
    id: UUID
    arquivo: str
    tamanho_bytes: int
    enviado_por: str
    enviado_em: datetime
    minha: bool                              # foi quem está logado que enviou
    status: SituacaoDaImportacao
    mensagem: str | None                     # o motivo, quando não carregou
    avisos: int                              # o que entrou, mas é para conferir (detalhe na página Pendências)
    quarentena: int                          # linhas que não entraram nos números
    fazendas: list[str]                      # as fazendas que a planilha alimentou
    iniciado_em: datetime | None
    finalizado_em: datetime | None
