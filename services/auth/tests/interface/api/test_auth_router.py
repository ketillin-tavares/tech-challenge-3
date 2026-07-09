"""Testes do router de auth (register/login) com IdentityProvider mockado."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.application.dtos.auth import TokensDTO
from src.application.ports.identity_provider import IdentityProvider
from src.domain.exceptions import ClienteJaExisteError, CredenciaisInvalidasError
from src.interface.controllers.dependencies import get_identity_provider

_CREDENCIAIS = {"email": "cliente@example.com", "senha": "senhaSegura1"}


@pytest.mark.unit
def test_register_retorna_201_com_sub(app: FastAPI, client: TestClient) -> None:
    """Registro bem-sucedido retorna 201 com o sub."""
    # Arrange
    identity = AsyncMock(spec=IdentityProvider)
    identity.registrar.return_value = "sub-123"
    app.dependency_overrides[get_identity_provider] = lambda: identity

    # Act
    resposta = client.post("/v1/auth/register", json=_CREDENCIAIS)

    # Assert
    assert resposta.status_code == 201
    assert resposta.json()["sub"] == "sub-123"


@pytest.mark.unit
def test_register_email_existente_retorna_409(app: FastAPI, client: TestClient) -> None:
    """E-mail ja cadastrado resulta em 409."""
    # Arrange
    identity = AsyncMock(spec=IdentityProvider)
    identity.registrar.side_effect = ClienteJaExisteError("cliente@example.com")
    app.dependency_overrides[get_identity_provider] = lambda: identity

    # Act
    resposta = client.post("/v1/auth/register", json=_CREDENCIAIS)

    # Assert
    assert resposta.status_code == 409
    assert resposta.json()["code"] == "CLIENTE_JA_EXISTE"


@pytest.mark.unit
def test_login_retorna_200_com_tokens(app: FastAPI, client: TestClient) -> None:
    """Login bem-sucedido retorna 200 com os tokens."""
    # Arrange
    identity = AsyncMock(spec=IdentityProvider)
    identity.autenticar.return_value = TokensDTO(
        id_token="id",
        access_token="acc",
        refresh_token="ref",
        token_type="Bearer",
        expires_in=3600,
    )
    app.dependency_overrides[get_identity_provider] = lambda: identity

    # Act
    resposta = client.post("/v1/auth/login", json=_CREDENCIAIS)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["access_token"] == "acc"


@pytest.mark.unit
def test_login_credenciais_invalidas_retorna_401(app: FastAPI, client: TestClient) -> None:
    """Credenciais invalidas resultam em 401."""
    # Arrange
    identity = AsyncMock(spec=IdentityProvider)
    identity.autenticar.side_effect = CredenciaisInvalidasError()
    app.dependency_overrides[get_identity_provider] = lambda: identity

    # Act
    resposta = client.post("/v1/auth/login", json=_CREDENCIAIS)

    # Assert
    assert resposta.status_code == 401
    assert resposta.json()["code"] == "CREDENCIAIS_INVALIDAS"
