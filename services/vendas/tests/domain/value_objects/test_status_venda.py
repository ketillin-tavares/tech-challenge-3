"""Testes do value object StatusVenda."""

import pytest

from src.domain.value_objects import StatusVenda


@pytest.mark.unit
def test_status_venda_pendente() -> None:
    """StatusVenda.PENDENTE existe e tem valor correto."""
    # Act
    status = StatusVenda.PENDENTE

    # Assert
    assert status == "PENDENTE"
    assert str(status) == "PENDENTE"


@pytest.mark.unit
def test_status_venda_paga() -> None:
    """StatusVenda.PAGA existe e tem valor correto."""
    # Act
    status = StatusVenda.PAGA

    # Assert
    assert status == "PAGA"
    assert str(status) == "PAGA"


@pytest.mark.unit
def test_status_venda_cancelada() -> None:
    """StatusVenda.CANCELADA existe e tem valor correto."""
    # Act
    status = StatusVenda.CANCELADA

    # Assert
    assert status == "CANCELADA"
    assert str(status) == "CANCELADA"


@pytest.mark.unit
def test_status_venda_sao_string_enum() -> None:
    """StatusVenda valores são strings (StrEnum)."""
    # Assert
    assert isinstance(StatusVenda.PENDENTE, str)
    assert isinstance(StatusVenda.PAGA, str)
    assert isinstance(StatusVenda.CANCELADA, str)
