"""Testes do Value Object Preco."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.domain.value_objects import Preco


@pytest.mark.unit
@pytest.mark.parametrize("valor", ["0", "-1", "-0.01"])
def test_preco_rejeita_valor_nao_positivo(valor: str) -> None:
    """Preco deve ser estritamente positivo."""
    with pytest.raises(ValidationError):
        Preco(valor=Decimal(valor))


@pytest.mark.unit
def test_preco_rejeita_mais_de_duas_casas_decimais() -> None:
    """Preco aceita no maximo 2 casas decimais."""
    with pytest.raises(ValidationError):
        Preco(valor=Decimal("10.123"))


@pytest.mark.unit
def test_preco_valido_e_imutavel() -> None:
    """Preco valido e congelado (frozen)."""
    # Arrange
    preco = Preco(valor=Decimal("99.90"))

    # Act / Assert
    assert preco.valor == Decimal("99.90")
    with pytest.raises(ValidationError):
        preco.valor = Decimal("1.00")
