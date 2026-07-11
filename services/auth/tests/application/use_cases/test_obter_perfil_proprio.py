"""Testes unitarios do caso de uso ObterPerfilProprio."""

from unittest.mock import AsyncMock

import pytest

from src.application.dtos.auth import PerfilClienteDTO
from src.application.ports.identity_provider import IdentityProvider
from src.application.use_cases.obter_perfil_proprio import ObterPerfilProprio
from src.domain.exceptions import TokenInvalidoError


@pytest.mark.unit
async def test_obter_perfil_proprio_sucesso() -> None:
    """Obtém perfil próprio com token valido."""
    # Arrange
    perfil = PerfilClienteDTO(
        sub="sub-123", email="cliente@example.com", nome="João Silva", cpf="12345678909"
    )
    identity = AsyncMock(spec=IdentityProvider)
    identity.obter_perfil_proprio.return_value = perfil
    caso = ObterPerfilProprio(identity)

    # Act
    resultado = await caso.executar("token-abc123")

    # Assert
    assert resultado == perfil
    assert resultado.sub == "sub-123"
    assert resultado.nome == "João Silva"
    assert resultado.cpf == "12345678909"
    identity.obter_perfil_proprio.assert_called_once_with("token-abc123")


@pytest.mark.unit
async def test_obter_perfil_proprio_sem_cpf() -> None:
    """Perfil legado pode ter cpf None (usuario antes da coleta)."""
    # Arrange
    perfil = PerfilClienteDTO(
        sub="sub-456", email="cliente@example.com", nome="Maria Silva", cpf=None
    )
    identity = AsyncMock(spec=IdentityProvider)
    identity.obter_perfil_proprio.return_value = perfil
    caso = ObterPerfilProprio(identity)

    # Act
    resultado = await caso.executar("token-xyz")

    # Assert
    assert resultado.cpf is None
    assert resultado.nome == "Maria Silva"


@pytest.mark.unit
async def test_obter_perfil_proprio_token_invalido() -> None:
    """Token invalido levanta TokenInvalidoError."""
    # Arrange
    identity = AsyncMock(spec=IdentityProvider)
    identity.obter_perfil_proprio.side_effect = TokenInvalidoError()
    caso = ObterPerfilProprio(identity)

    # Act / Assert
    with pytest.raises(TokenInvalidoError):
        await caso.executar("token-inválido")
