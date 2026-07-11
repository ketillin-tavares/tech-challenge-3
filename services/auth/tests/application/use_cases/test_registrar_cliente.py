"""Testes unitarios do caso de uso RegistrarCliente."""

from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from src.application.dtos.auth import ClienteRegistradoDTO, RegistrarClienteCommand
from src.application.ports.identity_provider import IdentityProvider
from src.application.use_cases.registrar_cliente import RegistrarCliente
from src.domain.exceptions import ClienteJaExisteError
from src.domain.value_objects import Cpf


@pytest.mark.unit
async def test_registrar_cliente_sucesso() -> None:
    """Registro bem-sucedido retorna DTO com CPF normalizado."""
    # Arrange
    identity = AsyncMock(spec=IdentityProvider)
    identity.registrar.return_value = "sub-123"
    caso = RegistrarCliente(identity)
    comando = RegistrarClienteCommand(
        email="cliente@example.com",
        senha="senhaSegura1",
        nome="João Silva",
        cpf="12345678909",
    )

    # Act
    resultado = await caso.executar(comando)

    # Assert
    assert isinstance(resultado, ClienteRegistradoDTO)
    assert resultado.sub == "sub-123"
    assert resultado.nome == "João Silva"
    assert resultado.cpf == "12345678909"
    # Verifica que o port recebeu Cpf VO normalizado
    call_args = identity.registrar.call_args
    cpf_arg = call_args[0][3]
    assert isinstance(cpf_arg, Cpf)
    assert cpf_arg.valor == "12345678909"


@pytest.mark.unit
async def test_registrar_cliente_cpf_formatado_normaliza() -> None:
    """CPF formatado no comando e normalizado antes do port."""
    # Arrange
    identity = AsyncMock(spec=IdentityProvider)
    identity.registrar.return_value = "sub-456"
    caso = RegistrarCliente(identity)
    comando = RegistrarClienteCommand(
        email="cliente@example.com",
        senha="senhaSegura1",
        nome="Maria Silva",
        cpf="123.456.789-09",  # Formatado
    )

    # Act
    resultado = await caso.executar(comando)

    # Assert
    assert resultado.cpf == "12345678909"  # Normalizado
    call_args = identity.registrar.call_args
    cpf_arg = call_args[0][3]
    assert cpf_arg.valor == "12345678909"


@pytest.mark.unit
async def test_registrar_cliente_cpf_invalido() -> None:
    """CPF invalido levanta ValidationError (port nao e chamado)."""
    # Arrange
    identity = AsyncMock(spec=IdentityProvider)
    caso = RegistrarCliente(identity)
    comando = RegistrarClienteCommand(
        email="cliente@example.com",
        senha="senhaSegura1",
        nome="João Silva",
        cpf="12345678900",  # Verificador errado
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        await caso.executar(comando)
    # Port nao deve ser chamado
    identity.registrar.assert_not_called()


@pytest.mark.unit
async def test_registrar_cliente_email_existente() -> None:
    """Email ja existente levanta ClienteJaExisteError."""
    # Arrange
    identity = AsyncMock(spec=IdentityProvider)
    identity.registrar.side_effect = ClienteJaExisteError()
    caso = RegistrarCliente(identity)
    comando = RegistrarClienteCommand(
        email="cliente@example.com",
        senha="senhaSegura1",
        nome="João Silva",
        cpf="12345678909",
    )

    # Act / Assert
    with pytest.raises(ClienteJaExisteError):
        await caso.executar(comando)
