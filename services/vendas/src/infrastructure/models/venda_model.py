"""Modelo ORM da tabela `vendas`."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.models.base import Base


class VendaModel(Base):
    """Modelo ORM para a tabela `vendas`.

    A constraint UNIQUE em `veiculo_id` impede a dupla venda do mesmo veiculo
    (defesa contra concorrencia no nivel do banco).
    """

    __tablename__ = "vendas"
    __table_args__ = (UniqueConstraint("veiculo_id", name="uq_vendas_veiculo_id"),)

    id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    veiculo_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("veiculos.id"),
        nullable=False,
    )
    cliente_id: Mapped[str] = mapped_column(String, nullable=False)
    preco_venda: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    data_venda: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
