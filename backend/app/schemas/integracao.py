"""Formato da tela de integrações (só o admin): as APIs que alimentam o painel e o histórico das cargas de cada uma."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

SituacaoDaCarga = Literal["pendente", "processando", "concluido", "concluido_com_avisos", "erro"]
SituacaoDaUnidade = Literal["carregada", "carregada_com_avisos", "inalterada", "ignorada", "erro"]


class IntegracaoPorApi(BaseModel):
    """Uma API que alimenta o painel (hoje, o Metryx). As planilhas não entram: chegam pela tela de importação."""
    fonte: str                              # o código da fonte nas cargas ("metryx")
    rotulo: str                             # o nome na tela ("Metryx")
    ligada: bool                            # a agenda preenchida: a autorização para chamar a API real
    quando: str                             # a agenda em palavras ("todo dia às 03:00, horário de Cuiabá")
    variavel_da_agenda: str                 # onde ligar, no .env do servidor ("AGENDA_METRYX")


class UnidadeDaCarga(BaseModel):
    """Um cliente (ou um arquivo) dentro de uma carga."""
    nome: str
    status: SituacaoDaUnidade
    erro: str | None                        # o motivo, quando não carregou
    avisos: int                             # o que entrou, mas é para conferir


class AvisoDaCarga(BaseModel):
    """Os erros e avisos de uma carga, agrupados pelo código."""
    nivel: Literal["erro", "aviso"]
    codigo: str
    problema: str                           # o código em palavras
    quantidade: int
    exemplo: str                            # a mensagem de uma das ocorrências


class CargaDaIntegracao(BaseModel):
    """Uma carga de uma API: quando rodou, quem pediu, o que fez com cada cliente e o que avisou."""
    id: UUID
    status: SituacaoDaCarga
    iniciado_em: datetime | None
    finalizado_em: datetime | None
    pedida_por: str | None                  # quem apertou "Atualizar agora"; None = a agenda ou a linha de comando
    unidades: list[UnidadeDaCarga]
    avisos: list[AvisoDaCarga]
