"""venda lifecycle (status PENDENTE/PAGA/CANCELADA + reserva com prazo)

Revision ID: 002
Revises: 001
Create Date: 2026-07-10 00:00:00.000000

Separa "compra" de "efetivacao da compra":
  - `vendas.status` (backfill PAGA: vendas pre-existentes ja eram concluidas);
  - `vendas.expira_em` (validade da reserva) e `vendas.updated_at`;
  - `vendas.data_venda` vira nullable (so preenchida na efetivacao);
  - a UNIQUE de `veiculo_id` vira indice unico PARCIAL (vendas CANCELADAS
    liberam o veiculo para recompra) + indice unico parcial de 1 venda
    PENDENTE por cliente (anti-abuso de reservas).

O downgrade exige ausencia de vendas CANCELADAS duplicadas por veiculo
(a constraint total nao as admite); e suportado apenas em desenvolvimento.
"""

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Adiciona o ciclo de vida da venda e os indices unicos parciais."""
    op.add_column("vendas", sa.Column("status", sa.String(length=10), nullable=True))
    op.execute("UPDATE vendas SET status = 'PAGA'")
    op.alter_column("vendas", "status", nullable=False)

    op.add_column("vendas", sa.Column("expira_em", sa.DateTime(timezone=True), nullable=True))

    op.add_column("vendas", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
    op.execute("UPDATE vendas SET updated_at = created_at")
    op.alter_column("vendas", "updated_at", nullable=False)

    op.alter_column("vendas", "data_venda", nullable=True)

    op.drop_constraint("uq_vendas_veiculo_id", "vendas", type_="unique")
    op.create_index(
        "uq_vendas_veiculo_id_ativa",
        "vendas",
        ["veiculo_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDENTE', 'PAGA')"),
    )
    op.create_index(
        "uq_vendas_cliente_pendente",
        "vendas",
        ["cliente_id"],
        unique=True,
        postgresql_where=sa.text("status = 'PENDENTE'"),
    )


def downgrade() -> None:
    """Remove o ciclo de vida da venda (somente desenvolvimento)."""
    op.drop_index("uq_vendas_cliente_pendente", table_name="vendas")
    op.drop_index("uq_vendas_veiculo_id_ativa", table_name="vendas")
    op.create_unique_constraint("uq_vendas_veiculo_id", "vendas", ["veiculo_id"])

    op.execute("UPDATE vendas SET data_venda = created_at WHERE data_venda IS NULL")
    op.alter_column("vendas", "data_venda", nullable=False)

    op.drop_column("vendas", "updated_at")
    op.drop_column("vendas", "expira_em")
    op.drop_column("vendas", "status")
