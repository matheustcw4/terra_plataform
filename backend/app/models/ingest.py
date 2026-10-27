from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Integer, LargeBinary, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.core import AGORA, UUID_PK


class Job(Base):
    __tablename__ = "job"
    __table_args__ = {"schema": "ingest"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fonte: Mapped[str] = mapped_column(Text)
    tipo: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=text("'pendente'"))
    usuario_id: Mapped[UUID | None] = mapped_column(ForeignKey("core.usuario.id", ondelete="SET NULL"))
    parametros: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    detalhe: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    unidades_total: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    unidades_carregadas: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    unidades_inalteradas: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    unidades_com_erro: Mapped[int] = mapped_column(Integer, server_default=text("0"))
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
    iniciado_em: Mapped[datetime | None]
    finalizado_em: Mapped[datetime | None]


class UnidadeOrigem(Base):
    __tablename__ = "unidade_origem"
    __table_args__ = {"schema": "ingest"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fonte: Mapped[str] = mapped_column(Text)
    chave: Mapped[str] = mapped_column(Text)
    descricao: Mapped[str | None] = mapped_column(Text)
    metadados: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    assinatura: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=text("'ativa'"))
    ultima_versao_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("ingest.versao_origem.id", ondelete="SET NULL", use_alter=True)
    )
    primeiro_visto_em: Mapped[datetime] = mapped_column(**AGORA)
    ultimo_visto_em: Mapped[datetime] = mapped_column(**AGORA)


class VersaoOrigem(Base):
    __tablename__ = "versao_origem"
    __table_args__ = {"schema": "ingest"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    unidade_id: Mapped[UUID] = mapped_column(ForeignKey("ingest.unidade_origem.id", ondelete="CASCADE"))
    sha256: Mapped[str] = mapped_column(Text)
    tamanho_bytes: Mapped[int | None] = mapped_column(BigInteger)
    metadados: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(Text, server_default=text("'extraida'"))
    job_id: Mapped[UUID | None] = mapped_column(ForeignKey("ingest.job.id", ondelete="SET NULL"))
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
    carregado_em: Mapped[datetime | None]


class Ocorrencia(Base):
    __tablename__ = "ocorrencia"
    __table_args__ = {"schema": "ingest"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    job_id: Mapped[UUID | None] = mapped_column(ForeignKey("ingest.job.id", ondelete="CASCADE"))
    versao_origem_id: Mapped[UUID | None] = mapped_column(ForeignKey("ingest.versao_origem.id", ondelete="CASCADE"))
    fazenda_id: Mapped[UUID | None] = mapped_column(ForeignKey("core.fazenda.id", ondelete="CASCADE"))
    nivel: Mapped[str] = mapped_column(Text)
    codigo: Mapped[str] = mapped_column(Text)
    mensagem: Mapped[str] = mapped_column(Text)
    entidade: Mapped[str | None] = mapped_column(Text)
    origem_linha: Mapped[str | None] = mapped_column(Text)
    contexto: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    criado_em: Mapped[datetime] = mapped_column(**AGORA)


class LinhaQuarentena(Base):
    __tablename__ = "linha_quarentena"
    __table_args__ = {"schema": "ingest"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    versao_origem_id: Mapped[UUID] = mapped_column(ForeignKey("ingest.versao_origem.id", ondelete="CASCADE"))
    job_id: Mapped[UUID | None] = mapped_column(ForeignKey("ingest.job.id", ondelete="SET NULL"))
    fazenda_id: Mapped[UUID | None] = mapped_column(ForeignKey("core.fazenda.id", ondelete="CASCADE"))
    entidade: Mapped[str] = mapped_column(Text)
    origem_linha: Mapped[str | None] = mapped_column(Text)
    codigo: Mapped[str] = mapped_column(Text)
    motivo: Mapped[str] = mapped_column(Text)
    dados: Mapped[dict[str, Any]] = mapped_column(JSONB)
    criado_em: Mapped[datetime] = mapped_column(**AGORA)


class Payload(Base):
    __tablename__ = "payload"
    __table_args__ = {"schema": "raw"}

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    recebido_em: Mapped[datetime] = mapped_column(primary_key=True, **AGORA)
    versao_origem_id: Mapped[UUID] = mapped_column(ForeignKey("ingest.versao_origem.id", ondelete="CASCADE"))
    fonte: Mapped[str] = mapped_column(Text)
    endpoint: Mapped[str | None] = mapped_column(Text)
    http_status: Mapped[int | None] = mapped_column(Integer)
    qtd_itens: Mapped[int | None] = mapped_column(Integer)
    conteudo: Mapped[Any] = mapped_column(JSONB)


class MetryxCredencial(Base):
    __tablename__ = "metryx_credencial"
    __table_args__ = {"schema": "integracao"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("core.cliente.id", ondelete="CASCADE"))
    metryx_customer_id: Mapped[str] = mapped_column(Text)
    token_cifrado: Mapped[bytes] = mapped_column(LargeBinary)
    token_impressao: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, server_default=text("'ativa'"))
    ultima_validacao_em: Mapped[datetime | None]
    ultimo_erro: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
    atualizado_em: Mapped[datetime] = mapped_column(**AGORA)
