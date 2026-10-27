from datetime import datetime
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, SmallInteger, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

UUID_PK = {"primary_key": True, "server_default": text("gen_random_uuid()")}
AGORA = {"server_default": text("now()")}


class Cliente(Base):
    __tablename__ = "cliente"
    __table_args__ = {"schema": "core"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    codigo: Mapped[int | None] = mapped_column(Integer, unique=True)
    nome: Mapped[str] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(server_default=text("true"))
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
    atualizado_em: Mapped[datetime] = mapped_column(**AGORA)


class Fazenda(Base):
    __tablename__ = "fazenda"
    __table_args__ = {"schema": "core"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("core.cliente.id"))
    nome: Mapped[str] = mapped_column(Text)
    proprietario: Mapped[str | None] = mapped_column(Text)
    sistema_produtivo: Mapped[str | None] = mapped_column(Text)
    tipo_ano: Mapped[str | None] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(server_default=text("true"))
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
    atualizado_em: Mapped[datetime] = mapped_column(**AGORA)


class Retiro(Base):
    __tablename__ = "retiro"
    __table_args__ = {"schema": "core"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fazenda_id: Mapped[UUID] = mapped_column(ForeignKey("core.fazenda.id", ondelete="CASCADE"))
    nome: Mapped[str] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(server_default=text("true"))
    criado_em: Mapped[datetime] = mapped_column(**AGORA)


class Funcao(Base):
    """O cadastro de funções do qual sai a função de cada usuário (só o admin edita)."""
    __tablename__ = "funcao"
    __table_args__ = {"schema": "core"}

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    nome: Mapped[str] = mapped_column(Text)
    ativo: Mapped[bool] = mapped_column(server_default=text("true"))
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
    atualizado_em: Mapped[datetime] = mapped_column(**AGORA)


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = {"schema": "core"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    email: Mapped[str] = mapped_column(Text)
    nome: Mapped[str] = mapped_column(Text)
    senha_hash: Mapped[str | None] = mapped_column(Text)
    funcao_id: Mapped[int | None] = mapped_column(SmallInteger, ForeignKey("core.funcao.id", ondelete="RESTRICT"))
    eh_admin: Mapped[bool] = mapped_column(server_default=text("false"))
    ativo: Mapped[bool] = mapped_column(server_default=text("true"))
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
    atualizado_em: Mapped[datetime] = mapped_column(**AGORA)


class UsuarioFazenda(Base):
    __tablename__ = "usuario_fazenda"
    __table_args__ = {"schema": "core"}

    usuario_id: Mapped[UUID] = mapped_column(ForeignKey("core.usuario.id", ondelete="CASCADE"), primary_key=True)
    fazenda_id: Mapped[UUID] = mapped_column(ForeignKey("core.fazenda.id", ondelete="CASCADE"), primary_key=True)
    papel: Mapped[str] = mapped_column(Text, server_default=text("'cliente'"))
    criado_em: Mapped[datetime] = mapped_column(**AGORA)


class FonteVinculo(Base):
    __tablename__ = "fonte_vinculo"
    __table_args__ = {"schema": "core"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fonte: Mapped[str] = mapped_column(Text)
    entidade: Mapped[str] = mapped_column(Text)
    id_externo: Mapped[str] = mapped_column(Text)
    entidade_id: Mapped[UUID]
    nome_externo: Mapped[str | None] = mapped_column(Text)
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
    atualizado_em: Mapped[datetime] = mapped_column(**AGORA)


class FazendaFonte(Base):
    __tablename__ = "fazenda_fonte"
    __table_args__ = {"schema": "core"}

    fazenda_id: Mapped[UUID] = mapped_column(ForeignKey("core.fazenda.id", ondelete="CASCADE"), primary_key=True)
    dominio: Mapped[str] = mapped_column(Text, primary_key=True)
    fonte: Mapped[str] = mapped_column(Text)
    atualizado_em: Mapped[datetime] = mapped_column(**AGORA)
