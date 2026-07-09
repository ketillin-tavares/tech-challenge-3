"""Testes da entidade Venda (imutabilidade)."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.domain.entities import Venda
from src.domain.value_objects import Preco


@pytest.mark.unit
def test_venda_e_imutavel() -> None:
    """Venda e um registro imutavel (frozen)."""
    # Arrange
    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-abc-123",
        preco_venda=Preco(valor=Decimal("85000.00")),
        data_venda=agora,
        created_at=agora,
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        venda.cliente_id = "outro"
