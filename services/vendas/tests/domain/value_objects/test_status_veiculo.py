"""Testes do Value Object StatusVeiculo."""

import pytest

from src.domain.value_objects import StatusVeiculo


@pytest.mark.unit
def test_status_veiculo_possui_apenas_dois_estados() -> None:
    """O enum cobre exatamente DISPONIVEL e VENDIDO."""
    assert {s.value for s in StatusVeiculo} == {"DISPONIVEL", "VENDIDO"}
