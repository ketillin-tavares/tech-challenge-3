"""create initial tables

Revision ID: 001
Revises:
Create Date: 2026-06-16 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Cria as tabelas `veiculos` e `vendas`."""
    op.create_table(
        "veiculos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marca", sa.String(), nullable=False),
        sa.Column("modelo", sa.String(), nullable=False),
        sa.Column("ano", sa.Integer(), nullable=False),
        sa.Column("cor", sa.String(), nullable=False),
        sa.Column("preco", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_veiculos_status_preco", "veiculos", ["status", "preco"])
    op.create_table(
        "vendas",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("veiculo_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("preco_venda", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("data_venda", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["veiculo_id"], ["veiculos.id"]),
        sa.UniqueConstraint("veiculo_id", name="uq_vendas_veiculo_id"),
    )


def downgrade() -> None:
    """Remove as tabelas `vendas` e `veiculos`."""
    op.drop_table("vendas")
    op.drop_index("idx_veiculos_status_preco", table_name="veiculos")
    op.drop_table("veiculos")
