"""Modelo ORM da tabela `vendas`."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.models.base import Base


class VendaModel(Base):
    """Modelo ORM para a tabela `vendas`.

    Dois indices unicos PARCIAIS defendem as invariantes sob concorrencia:
      - `uq_vendas_veiculo_id_ativa`: no maximo UMA venda ativa (PENDENTE ou
        PAGA) por veiculo -- vendas CANCELADAS liberam o veiculo para recompra.
      - `uq_vendas_cliente_pendente`: no maximo UMA venda PENDENTE por cliente
        (anti-abuso: impede um cliente de reservar o estoque inteiro).
    """

    __tablename__ = "vendas"
    __table_args__ = (
        Index(
            "uq_vendas_veiculo_id_ativa",
            "veiculo_id",
            unique=True,
            postgresql_where=text("status IN ('PENDENTE', 'PAGA')"),
        ),
        Index(
            "uq_vendas_cliente_pendente",
            "cliente_id",
            unique=True,
            postgresql_where=text("status = 'PENDENTE'"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    veiculo_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("veiculos.id"),
        nullable=False,
    )
    cliente_id: Mapped[str] = mapped_column(String, nullable=False)
    preco_venda: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    expira_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    data_venda: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
