"""Testes do router de clientes (GET /v1/clientes/me e /v1/clientes/{sub})."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.application.dtos.auth import PerfilClienteDTO
from src.application.ports.identity_provider import IdentityProvider
from src.domain.exceptions import ClienteNaoEncontradoError
from src.domain.value_objects import ClienteAutenticado
from src.interface.controllers.dependencies import (
    get_identity_provider,
    get_token_verifier,
)


class FakeTokenVerifier:
    """Verifier fake que retorna ClienteAutenticado mocado."""

    def __init__(self, sub: str = "sub-123", grupos: set[str] | None = None) -> None:
        self.sub = sub
        self.grupos = grupos or set()

    def verificar(self, token: str) -> ClienteAutenticado:
        """Retorna ClienteAutenticado com sub e grupos."""
        return ClienteAutenticado(sub=self.sub, grupos=self.grupos)


@pytest.mark.unit
def test_obter_perfil_proprio_sucesso(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """GET /v1/clientes/me retorna perfil com CPF mascarado."""
    # Arrange
    token_verifier = FakeTokenVerifier(sub="sub-123")
    identity = AsyncMock(spec=IdentityProvider)
    identity.obter_perfil_proprio.return_value = PerfilClienteDTO(
        sub="sub-123", email="cliente@example.com", nome="João Silva", cpf="12345678909"
    )
    app.dependency_overrides[get_token_verifier] = lambda: token_verifier
    app.dependency_overrides[get_identity_provider] = lambda: identity
    monkeypatch.setenv("RATELIMIT_ENABLED", "false")

    # Act
    resposta = client.get("/v1/clientes/me", headers={"Authorization": "Bearer token-teste"})

    # Assert
    assert resposta.status_code == 200
    body = resposta.json()
    assert body["sub"] == "sub-123"
    assert body["nome"] == "João Silva"
    assert body["cpf"] == "123.***.***-09"  # CPF mascarado


@pytest.mark.unit
def test_obter_perfil_proprio_legado_sem_cpf(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """GET /v1/clientes/me com usuario legado (sem nome/cpf) retorna None."""
    # Arrange
    token_verifier = FakeTokenVerifier(sub="sub-456")
    identity = AsyncMock(spec=IdentityProvider)
    identity.obter_perfil_proprio.return_value = PerfilClienteDTO(
        sub="sub-456", email="cliente@example.com", nome=None, cpf=None
    )
    app.dependency_overrides[get_token_verifier] = lambda: token_verifier
    app.dependency_overrides[get_identity_provider] = lambda: identity
    monkeypatch.setenv("RATELIMIT_ENABLED", "false")

    # Act
    resposta = client.get("/v1/clientes/me", headers={"Authorization": "Bearer token-teste"})

    # Assert
    assert resposta.status_code == 200
    body = resposta.json()
    assert body["nome"] is None
    assert body["cpf"] is None


@pytest.mark.unit
def test_obter_perfil_proprio_sem_token(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """GET /v1/clientes/me sem token retorna 401."""
    # Arrange
    monkeypatch.setenv("RATELIMIT_ENABLED", "false")

    # Act
    resposta = client.get("/v1/clientes/me")

    # Assert
    assert resposta.status_code == 401


@pytest.mark.unit
def test_obter_perfil_por_sub_admin_sucesso(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """GET /v1/clientes/{sub} admin retorna CPF completo."""
    # Arrange
    token_verifier = FakeTokenVerifier(sub="sub-admin", grupos={"admin"})
    identity = AsyncMock(spec=IdentityProvider)
    identity.obter_perfil_por_sub.return_value = PerfilClienteDTO(
        sub="sub-123", email="cliente@example.com", nome="João Silva", cpf="12345678909"
    )
    app.dependency_overrides[get_token_verifier] = lambda: token_verifier
    app.dependency_overrides[get_identity_provider] = lambda: identity
    monkeypatch.setenv("RATELIMIT_ENABLED", "false")

    # Act
    resposta = client.get("/v1/clientes/sub-123", headers={"Authorization": "Bearer token-admin"})

    # Assert
    assert resposta.status_code == 200
    body = resposta.json()
    assert body["cpf"] == "12345678909"  # Completo, nao mascarado


@pytest.mark.unit
def test_obter_perfil_por_sub_sem_admin_retorna_403(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """GET /v1/clientes/{sub} sem admin retorna 403."""
    # Arrange
    token_verifier = FakeTokenVerifier(sub="sub-usuario")  # Sem grupo admin
    identity = AsyncMock(spec=IdentityProvider)
    app.dependency_overrides[get_token_verifier] = lambda: token_verifier
    app.dependency_overrides[get_identity_provider] = lambda: identity
    monkeypatch.setenv("RATELIMIT_ENABLED", "false")

    # Act
    resposta = client.get("/v1/clientes/sub-123", headers={"Authorization": "Bearer token-usuario"})

    # Assert
    assert resposta.status_code == 403


@pytest.mark.unit
def test_obter_perfil_por_sub_inexistente_retorna_404(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """GET /v1/clientes/{sub} inexistente retorna 404 CLIENTE_NAO_ENCONTRADO."""
    # Arrange
    token_verifier = FakeTokenVerifier(sub="sub-admin", grupos={"admin"})
    identity = AsyncMock(spec=IdentityProvider)
    identity.obter_perfil_por_sub.side_effect = ClienteNaoEncontradoError()
    app.dependency_overrides[get_token_verifier] = lambda: token_verifier
    app.dependency_overrides[get_identity_provider] = lambda: identity
    monkeypatch.setenv("RATELIMIT_ENABLED", "false")

    # Act
    resposta = client.get(
        "/v1/clientes/sub-inexistente", headers={"Authorization": "Bearer token-admin"}
    )

    # Assert
    assert resposta.status_code == 404
    assert resposta.json()["code"] == "CLIENTE_NAO_ENCONTRADO"
