from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import CHAR, Computed, ForeignKey, Numeric, SmallInteger, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.db.base import Base
from app.models.core import AGORA, UUID_PK

QTD = Numeric(14, 3)
PESO = Numeric(16, 3)
AREA = Numeric(12, 3)
VALOR = Numeric(16, 2)


class ColunasTecnicas:
    """Rastreabilidade comum a todos os fatos carregados por adapter."""

    fonte: Mapped[str] = mapped_column(Text)

    @declared_attr
    def origem_ref(cls) -> Mapped[UUID]:
        return mapped_column(ForeignKey("ingest.versao_origem.id"))

    origem_linha: Mapped[str] = mapped_column(Text)
    extra: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ingest_job_id: Mapped[UUID | None]
    carregado_em: Mapped[datetime] = mapped_column(**AGORA)


class MovAnimal(ColunasTecnicas, Base):
    __tablename__ = "mov_animal"
    __table_args__ = {"schema": "fato"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fazenda_id: Mapped[UUID] = mapped_column(ForeignKey("core.fazenda.id"))
    retiro_id: Mapped[UUID | None] = mapped_column(ForeignKey("core.retiro.id"))
    cenario: Mapped[str] = mapped_column(Text)
    versao_plano_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim.versao_plano.id"))
    tipo: Mapped[str] = mapped_column(Text)
    data: Mapped[date]
    competencia: Mapped[date] = mapped_column(Computed("date_trunc('month', data::timestamp)::date"))
    categoria_map_id: Mapped[UUID] = mapped_column(ForeignKey("dim.categoria_map.id"))
    categoria_destino_map_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim.categoria_map.id"))
    qtd: Mapped[Decimal] = mapped_column(QTD)
    peso_vivo_total_kg: Mapped[Decimal | None] = mapped_column(PESO)
    peso_carcaca_total_kg: Mapped[Decimal | None] = mapped_column(PESO)
    valor_total: Mapped[Decimal | None] = mapped_column(VALOR)
    contraparte: Mapped[str | None] = mapped_column(Text)
    documento: Mapped[str | None] = mapped_column(Text)
    causa: Mapped[str | None] = mapped_column(Text)
    local: Mapped[str | None] = mapped_column(Text)
    era: Mapped[str | None] = mapped_column(Text)
    safra: Mapped[str | None] = mapped_column(Text)


class Inventario(ColunasTecnicas, Base):
    __tablename__ = "inventario"
    __table_args__ = {"schema": "fato"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fazenda_id: Mapped[UUID] = mapped_column(ForeignKey("core.fazenda.id"))
    retiro_id: Mapped[UUID | None] = mapped_column(ForeignKey("core.retiro.id"))
    categoria_map_id: Mapped[UUID] = mapped_column(ForeignKey("dim.categoria_map.id"))
    data: Mapped[date]
    qtd: Mapped[Decimal] = mapped_column(QTD)


class RebanhoMedioMensal(ColunasTecnicas, Base):
    __tablename__ = "rebanho_medio_mensal"
    __table_args__ = {"schema": "fato"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fazenda_id: Mapped[UUID] = mapped_column(ForeignKey("core.fazenda.id"))
    cenario: Mapped[str] = mapped_column(Text)
    versao_plano_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim.versao_plano.id"))
    competencia: Mapped[date]
    grupo: Mapped[str | None] = mapped_column(Text)
    categoria_map_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim.categoria_map.id"))
    qtd_cab: Mapped[Decimal] = mapped_column(QTD)
    peso_vivo_total_kg: Mapped[Decimal | None] = mapped_column(PESO)
    qtd_ua_informada: Mapped[Decimal | None] = mapped_column(QTD)


class AreaMensal(ColunasTecnicas, Base):
    __tablename__ = "area_mensal"
    __table_args__ = {"schema": "fato"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fazenda_id: Mapped[UUID] = mapped_column(ForeignKey("core.fazenda.id"))
    cenario: Mapped[str] = mapped_column(Text)
    versao_plano_id: Mapped[UUID | None] = mapped_column(ForeignKey("dim.versao_plano.id"))
    competencia: Mapped[date]
    area_pasto_ha: Mapped[Decimal | None] = mapped_column(AREA)
    area_ilp_ha: Mapped[Decimal | None] = mapped_column(AREA)
    area_total_ha: Mapped[Decimal | None] = mapped_column(AREA)
    area_produtiva_ha: Mapped[Decimal | None] = mapped_column(AREA)


class LancamentoFinanceiro(ColunasTecnicas, Base):
    __tablename__ = "lancamento_financeiro"
    __table_args__ = {"schema": "fato"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fazenda_id: Mapped[UUID] = mapped_column(ForeignKey("core.fazenda.id"))
    fazenda_fiscal_id: Mapped[UUID | None] = mapped_column(ForeignKey("core.fazenda.id"))
    plano_contas_map_id: Mapped[UUID] = mapped_column(ForeignKey("dim.plano_contas_map.id"))  # conta (de-para)
    natureza: Mapped[str] = mapped_column(CHAR(1))
    valor: Mapped[Decimal] = mapped_column(VALOR)
    data_pagamento: Mapped[date]
    data_vencimento: Mapped[date | None]
    competencia: Mapped[date] = mapped_column(Computed("date_trunc('month', data_pagamento::timestamp)::date"))
    descricao: Mapped[str | None] = mapped_column(Text)
    contraparte: Mapped[str | None] = mapped_column(Text)
    documento: Mapped[str | None] = mapped_column(Text)


class OrcamentoFinanceiro(ColunasTecnicas, Base):
    __tablename__ = "orcamento_financeiro"
    __table_args__ = {"schema": "fato"}

    id: Mapped[UUID] = mapped_column(**UUID_PK)
    fazenda_id: Mapped[UUID] = mapped_column(ForeignKey("core.fazenda.id"))
    versao_plano_id: Mapped[UUID] = mapped_column(ForeignKey("dim.versao_plano.id"))
    tipo: Mapped[str] = mapped_column(Text, server_default=text("'previsao'"))   # previsao | planejamento
    plano_contas_map_id: Mapped[UUID] = mapped_column(ForeignKey("dim.plano_contas_map.id"))  # conta (de-para)
    natureza: Mapped[str] = mapped_column(CHAR(1))
    competencia: Mapped[date]
    valor: Mapped[Decimal] = mapped_column(VALOR)


class EstoqueMensal(Base):
    __tablename__ = "estoque_mensal"
    __table_args__ = {"schema": "fato"}

    fazenda_id: Mapped[UUID] = mapped_column(ForeignKey("core.fazenda.id", ondelete="CASCADE"), primary_key=True)
    cenario: Mapped[str] = mapped_column(Text, primary_key=True)
    categoria_bi_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("dim.categoria_bi.id"), primary_key=True)
    competencia: Mapped[date] = mapped_column(primary_key=True)
    saldo_inicial: Mapped[Decimal] = mapped_column(QTD)
    compra: Mapped[Decimal] = mapped_column(QTD)
    nascimento: Mapped[Decimal] = mapped_column(QTD)
    transf_entrada: Mapped[Decimal] = mapped_column(QTD)
    desmame_entrada: Mapped[Decimal] = mapped_column(QTD)
    mudanca_entrada: Mapped[Decimal] = mapped_column(QTD)
    abate: Mapped[Decimal] = mapped_column(QTD)
    venda_em_pe: Mapped[Decimal] = mapped_column(QTD)
    morte: Mapped[Decimal] = mapped_column(QTD)
    consumo_doacao: Mapped[Decimal] = mapped_column(QTD)
    transf_saida: Mapped[Decimal] = mapped_column(QTD)
    desmame_saida: Mapped[Decimal] = mapped_column(QTD)
    mudanca_saida: Mapped[Decimal] = mapped_column(QTD)
    ajuste: Mapped[Decimal] = mapped_column(QTD)
    saldo_final: Mapped[Decimal] = mapped_column(QTD)
    calculado_em: Mapped[datetime] = mapped_column(**AGORA)
