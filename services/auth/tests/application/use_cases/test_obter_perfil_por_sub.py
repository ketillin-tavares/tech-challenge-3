"""Testes unitarios do caso de uso ObterPerfilPorSub."""

from unittest.mock import AsyncMock

import pytest

from src.application.dtos.auth import PerfilClienteDTO
from src.application.ports.identity_provider import IdentityProvider
from src.application.use_cases.obter_perfil_por_sub import ObterPerfilPorSub
from src.domain.exceptions import ClienteNaoEncontradoError


@pytest.mark.unit
async def test_obter_perfil_por_sub_sucesso() -> None:
    """Obtém perfil por sub com sucesso."""
    # Arrange
    perfil = PerfilClienteDTO(
        sub="sub-123", email="cliente@example.com", nome="João Silva", cpf="12345678909"
    )
    identity = AsyncMock(spec=IdentityProvider)
    identity.obter_perfil_por_sub.return_value = perfil
    caso = ObterPerfilPorSub(identity)

    # Act
    resultado = await caso.executar("sub-123")

    # Assert
    assert resultado == perfil
    assert resultado.sub == "sub-123"
    identity.obter_perfil_por_sub.assert_called_once_with("sub-123")


@pytest.mark.unit
async def test_obter_perfil_por_sub_inexistente() -> None:
    """Sub inexistente levanta ClienteNaoEncontradoError."""
    # Arrange
    identity = AsyncMock(spec=IdentityProvider)
    identity.obter_perfil_por_sub.return_value = None
    caso = ObterPerfilPorSub(identity)

    # Act / Assert
    with pytest.raises(ClienteNaoEncontradoError):
        await caso.executar("sub-inexistente")


@pytest.mark.unit
async def test_obter_perfil_por_sub_legado_sem_cpf() -> None:
    """Perfil legado pode ter cpf e nome None."""
    # Arrange
    perfil = PerfilClienteDTO(sub="sub-789", email="cliente@example.com", nome=None, cpf=None)
    identity = AsyncMock(spec=IdentityProvider)
    identity.obter_perfil_por_sub.return_value = perfil
    caso = ObterPerfilPorSub(identity)

    # Act
    resultado = await caso.executar("sub-789")

    # Assert
    assert resultado.cpf is None
    assert resultado.nome is None
    assert resultado.email == "cliente@example.com"
