"""Testes do Value Object Ano."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.domain.value_objects import ANO_MINIMO, Ano


@pytest.mark.unit
def test_ano_rejeita_abaixo_do_minimo() -> None:
    """Ano anterior a 1900 e invalido."""
    with pytest.raises(ValidationError):
        Ano(valor=ANO_MINIMO - 1)


@pytest.mark.unit
def test_ano_rejeita_futuro_distante() -> None:
    """Ano alem do proximo ano e invalido."""
    ano_invalido = datetime.now(UTC).year + 2
    with pytest.raises(ValidationError):
        Ano(valor=ano_invalido)


@pytest.mark.unit
def test_ano_aceita_proximo_ano() -> None:
    """Ano igual ao proximo ano (lancamentos) e valido."""
    proximo_ano = datetime.now(UTC).year + 1
    assert Ano(valor=proximo_ano).valor == proximo_ano
