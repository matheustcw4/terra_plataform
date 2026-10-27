from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import Computed, ForeignKey, Numeric, SmallInteger, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.core import AGORA, UUID_PK


class CategoriaBi(Base):
    __tablename__ = "categoria_bi"
    __table_args__ = {"schema": "dim"}

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, autoincrement=False)
    nome: Mapped[str] = mapped_column(Text, unique=True)
    sexo: Mapped[str] = mapped_column(Text)
    grupo: Mapped[str] = mapped_column(Text)
    era: Mapped[str] = mapped_column(Text)
    peso_ref_kg: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))


class CategoriaMap(Base):
    __tablename__ = "categoria_map"
    __table_args__ = {"schema": "dim"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fonte: Mapped[str] = mapped_column(Text)
    cliente_id: Mapped[UUID | None] = mapped_column(ForeignKey("core.cliente.id", ondelete="CASCADE"))
    fazenda_id: Mapped[UUID | None] = mapped_column(ForeignKey("core.fazenda.id", ondelete="CASCADE"))
    categoria_origem: Mapped[str] = mapped_column(Text)
    nome_origem: Mapped[str] = mapped_column(Text)
    categoria_bi_id: Mapped[int | None] = mapped_column(SmallInteger, ForeignKey("dim.categoria_bi.id"))
    categoria_bi_sugerida_id: Mapped[int | None] = mapped_column(SmallInteger, ForeignKey("dim.categoria_bi.id"))
    confirmado_por: Mapped[UUID | None] = mapped_column(ForeignKey("core.usuario.id"))
    confirmado_em: Mapped[datetime | None]
    atributos: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
    atualizado_em: Mapped[datetime] = mapped_column(**AGORA)


class CentroCusto(Base):
    __tablename__ = "centro_custo"
    __table_args__ = {"schema": "dim"}

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    nome: Mapped[str] = mapped_column(Text, unique=True)
    nome_normalizado: Mapped[str] = mapped_column(Text, Computed("app.normalizar(nome)"))
    classificacao: Mapped[str] = mapped_column(Text)
    entra_desembolso: Mapped[bool]
    entra_custeio: Mapped[bool]
    tipo_custeio: Mapped[str | None] = mapped_column(Text)
    eh_reposicao: Mapped[bool] = mapped_column(server_default=text("false"))
    ativo: Mapped[bool] = mapped_column(server_default=text("true"))


class Subcentro(Base):
    __tablename__ = "subcentro"
    __table_args__ = {"schema": "dim"}

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    centro_custo_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("dim.centro_custo.id"))
    nome: Mapped[str] = mapped_column(Text)
    nome_normalizado: Mapped[str] = mapped_column(Text, Computed("app.normalizar(nome)"))
    entra_desembolso: Mapped[bool | None]
    entra_custeio: Mapped[bool | None]
    tipo_custeio: Mapped[str | None] = mapped_column(Text)
    eh_reposicao: Mapped[bool | None]
    ativo: Mapped[bool] = mapped_column(server_default=text("true"))


class PlanoContasMap(Base):
    __tablename__ = "plano_contas_map"
    __table_args__ = {"schema": "dim"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fonte: Mapped[str] = mapped_column(Text)
    centro_origem: Mapped[str] = mapped_column(Text)
    subcentro_origem: Mapped[str] = mapped_column(Text, server_default=text("''"))
    # NULL = conta "A classificar" (pendente do admin)
    centro_custo_id: Mapped[int | None] = mapped_column(SmallInteger, ForeignKey("dim.centro_custo.id"))
    subcentro_id: Mapped[int | None] = mapped_column(SmallInteger, ForeignKey("dim.subcentro.id"))
    nome_centro_origem: Mapped[str | None] = mapped_column(Text)
    nome_subcentro_origem: Mapped[str | None] = mapped_column(Text)
    confirmado_por: Mapped[UUID | None] = mapped_column(ForeignKey("core.usuario.id"))
    confirmado_em: Mapped[datetime | None]
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
    atualizado_em: Mapped[datetime] = mapped_column(**AGORA)


class Calendario(Base):
    __tablename__ = "calendario"
    __table_args__ = {"schema": "dim"}

    data: Mapped[date] = mapped_column(primary_key=True)
    ano: Mapped[int] = mapped_column(SmallInteger)
    mes: Mapped[int] = mapped_column(SmallInteger)
    dia: Mapped[int] = mapped_column(SmallInteger)
    competencia: Mapped[date]
    ultimo_dia_mes: Mapped[date]
    nome_mes: Mapped[str] = mapped_column(Text)
    mes_abrev: Mapped[str] = mapped_column(Text)
    ano_mes: Mapped[str] = mapped_column(Text)
    rotulo_mes: Mapped[str] = mapped_column(Text)
    safra_inicio: Mapped[int] = mapped_column(SmallInteger)
    safra: Mapped[str] = mapped_column(Text)
    ordem_safra: Mapped[int] = mapped_column(SmallInteger)


class Parametro(Base):
    __tablename__ = "parametro"
    __table_args__ = {"schema": "dim"}

    chave: Mapped[str] = mapped_column(Text, primary_key=True)
    valor: Mapped[Decimal | None] = mapped_column(Numeric)
    valor_texto: Mapped[str | None] = mapped_column(Text)
    descricao: Mapped[str] = mapped_column(Text)
    atualizado_em: Mapped[datetime] = mapped_column(**AGORA)


class VersaoPlano(Base):
    __tablename__ = "versao_plano"
    __table_args__ = {"schema": "dim"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    cliente_id: Mapped[UUID] = mapped_column(ForeignKey("core.cliente.id", ondelete="CASCADE"))
    fonte: Mapped[str] = mapped_column(Text)
    codigo: Mapped[str] = mapped_column(Text)
    nome: Mapped[str | None] = mapped_column(Text)
    oficial: Mapped[bool] = mapped_column(server_default=text("false"))
    criado_em: Mapped[datetime] = mapped_column(**AGORA)
