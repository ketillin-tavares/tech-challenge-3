"""Testes do Value Object StatusVeiculo."""

import pytest

from src.domain.value_objects import StatusVeiculo


@pytest.mark.unit
def test_status_veiculo_possui_tres_estados() -> None:
    """O enum cobre exatamente DISPONIVEL, RESERVADO e VENDIDO."""
    assert {s.value for s in StatusVeiculo} == {"DISPONIVEL", "RESERVADO", "VENDIDO"}


@pytest.mark.unit
def test_status_veiculo_disponivel() -> None:
    """StatusVeiculo.DISPONIVEL existe e tem valor correto."""
    assert StatusVeiculo.DISPONIVEL == "DISPONIVEL"


@pytest.mark.unit
def test_status_veiculo_reservado() -> None:
    """StatusVeiculo.RESERVADO existe e tem valor correto."""
    assert StatusVeiculo.RESERVADO == "RESERVADO"


@pytest.mark.unit
def test_status_veiculo_vendido() -> None:
    """StatusVeiculo.VENDIDO existe e tem valor correto."""
    assert StatusVeiculo.VENDIDO == "VENDIDO"
