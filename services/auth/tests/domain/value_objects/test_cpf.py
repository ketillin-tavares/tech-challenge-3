"""Testes do value object Cpf."""

import pytest
from pydantic import ValidationError

from src.domain.value_objects import Cpf


@pytest.mark.unit
def test_cpf_valido_com_digitos() -> None:
    """CPF valido com 11 digitos e verificadores corretos."""
    cpf = Cpf(valor="12345678909")
    assert cpf.valor == "12345678909"


@pytest.mark.unit
def test_cpf_formatado_normaliza_para_digitos() -> None:
    """CPF formatado 'XXX.XXX.XXX-XX' normaliza para digitos apenas."""
    cpf = Cpf(valor="123.456.789-09")
    assert cpf.valor == "12345678909"


@pytest.mark.unit
def test_cpf_normalizado_e_formatado_equivalentes() -> None:
    """CPF normalizado e formatado sao equivalentes."""
    cpf_digitos = Cpf(valor="12345678909")
    cpf_formatado = Cpf(valor="123.456.789-09")
    assert cpf_digitos.valor == cpf_formatado.valor


@pytest.mark.unit
def test_cpf_invalido_verificador_errado() -> None:
    """CPF com verificador errado levanta ValidationError."""
    with pytest.raises(ValidationError):
        Cpf(valor="12345678900")


@pytest.mark.unit
def test_cpf_invalido_sequencia_repetida() -> None:
    """CPF com todos os digitos iguais levanta ValidationError."""
    with pytest.raises(ValidationError):
        Cpf(valor="11111111111")


@pytest.mark.unit
def test_cpf_invalido_tamanho_pequeno() -> None:
    """CPF com menos de 11 digitos levanta ValidationError."""
    with pytest.raises(ValidationError):
        Cpf(valor="123")


@pytest.mark.unit
def test_cpf_invalido_tamanho_grande() -> None:
    """CPF com mais de 11 digitos levanta ValidationError."""
    with pytest.raises(ValidationError):
        Cpf(valor="123456789090000")


@pytest.mark.unit
def test_cpf_frozen() -> None:
    """CPF e frozen (immutavel)."""
    cpf = Cpf(valor="12345678909")
    with pytest.raises(ValidationError):
        cpf.valor = "98765432100"
