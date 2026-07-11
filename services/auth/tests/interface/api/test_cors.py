"""Testes do middleware de CORS (registro condicional por variavel de ambiente)."""

import pytest
from fastapi.testclient import TestClient

from src.environment import get_settings
from src.main import create_app

_ORIGEM_PERMITIDA = "http://localhost:5173"


def _client_com_cors(monkeypatch: pytest.MonkeyPatch, origins: str) -> TestClient:
    """Cria um TestClient sobre uma app fresca com `CORS_ORIGINS` controlada.

    Args:
        monkeypatch: Fixture do pytest para alterar o ambiente.
        origins: Valor da env `CORS_ORIGINS` (vazio desabilita o middleware).

    Returns:
        TestClient da aplicacao recem-criada.
    """
    monkeypatch.setenv("CORS_ORIGINS", origins)
    get_settings.cache_clear()
    return TestClient(create_app())


@pytest.mark.unit
def test_origem_permitida_recebe_header_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Requisicao com Origin configurada recebe access-control-allow-origin."""
    # Arrange
    client = _client_com_cors(monkeypatch, _ORIGEM_PERMITIDA)

    # Act
    resposta = client.get("/health", headers={"Origin": _ORIGEM_PERMITIDA})

    # Assert
    assert resposta.headers.get("access-control-allow-origin") == _ORIGEM_PERMITIDA


@pytest.mark.unit
def test_preflight_de_origem_permitida_e_aceito(monkeypatch: pytest.MonkeyPatch) -> None:
    """OPTIONS (preflight) de origem permitida retorna os headers de CORS."""
    # Arrange
    client = _client_com_cors(monkeypatch, _ORIGEM_PERMITIDA)

    # Act
    resposta = client.options(
        "/v1/auth/login",
        headers={
            "Origin": _ORIGEM_PERMITIDA,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )

    # Assert
    assert resposta.status_code == 200
    assert resposta.headers.get("access-control-allow-origin") == _ORIGEM_PERMITIDA


@pytest.mark.unit
def test_origem_nao_listada_nao_recebe_header_cors(monkeypatch: pytest.MonkeyPatch) -> None:
    """Origem fora da lista nao recebe access-control-allow-origin."""
    # Arrange
    client = _client_com_cors(monkeypatch, _ORIGEM_PERMITIDA)

    # Act
    resposta = client.get("/health", headers={"Origin": "https://malicioso.example.com"})

    # Assert
    assert "access-control-allow-origin" not in resposta.headers


@pytest.mark.unit
def test_sem_cors_origins_middleware_nao_e_registrado(monkeypatch: pytest.MonkeyPatch) -> None:
    """Sem CORS_ORIGINS o middleware nao existe (comportamento pre-existente)."""
    # Arrange
    client = _client_com_cors(monkeypatch, "")

    # Act
    resposta = client.get("/health", headers={"Origin": _ORIGEM_PERMITIDA})

    # Assert
    assert "access-control-allow-origin" not in resposta.headers
