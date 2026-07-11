"""Testes do presenter de mascaramento de CPF."""

import pytest

from src.interface.presenters.cpf_presenter import mascarar_cpf


@pytest.mark.unit
def test_mascarar_cpf_valido() -> None:
    """Mascara CPF de 11 digitos corretamente."""
    resultado = mascarar_cpf("12345678909")
    assert resultado == "123.***.***-09"


@pytest.mark.unit
def test_mascarar_cpf_formatado() -> None:
    """Mascara CPF ja formatado."""
    resultado = mascarar_cpf("123.456.789-09")
    assert resultado == "123.***.***-09"


@pytest.mark.unit
def test_mascarar_cpf_tamanho_invalido_retorna_original() -> None:
    """CPF com tamanho != 11 retorna original (sem mascaramento)."""
    resultado = mascarar_cpf("123")
    assert resultado == "123"


@pytest.mark.unit
def test_mascarar_cpf_vazio_retorna_original() -> None:
    """CPF vazio retorna original."""
    resultado = mascarar_cpf("")
    assert resultado == ""
