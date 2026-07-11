"""Testes do router de veiculos (TestClient + dependency_overrides)."""

from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.application.use_cases.cadastrar_veiculo import CadastrarVeiculo
from src.application.use_cases.listar_disponiveis import ListarDisponiveis
from src.interface.controllers.dependencies import get_token_verifier
from src.interface.controllers.v1 import veiculos_controller
from tests.interface.conftest import (
    FakeTokenVerifier,
    construir_veiculo_dto,
)

_PAYLOAD = {
    "marca": "Toyota",
    "modelo": "Corolla",
    "ano": 2020,
    "cor": "Prata",
    "preco": "85000.00",
}
_AUTH = {"Authorization": "Bearer token-de-teste"}


@pytest.mark.unit
def test_cadastrar_veiculo_admin_retorna_201(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """Admin cadastra veiculo com sucesso (201)."""
    # Arrange
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(grupos=("admin",))
    caso = AsyncMock(spec=CadastrarVeiculo)
    caso.executar.return_value = construir_veiculo_dto()
    monkeypatch.setattr(veiculos_controller, "CadastrarVeiculo", lambda repo: caso)

    # Act
    resposta = client.post("/v1/veiculos", json=_PAYLOAD, headers=_AUTH)

    # Assert
    assert resposta.status_code == 201
    assert resposta.json()["status"] == "DISPONIVEL"


@pytest.mark.unit
def test_cadastrar_veiculo_sem_grupo_admin_retorna_403(app: FastAPI, client: TestClient) -> None:
    """Usuario autenticado sem grupo admin recebe 403."""
    # Arrange
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(grupos=())

    # Act
    resposta = client.post("/v1/veiculos", json=_PAYLOAD, headers=_AUTH)

    # Assert
    assert resposta.status_code == 403


@pytest.mark.unit
def test_cadastrar_veiculo_sem_token_retorna_401(app: FastAPI, client: TestClient) -> None:
    """Requisicao sem token recebe 401."""
    # Act
    resposta = client.post("/v1/veiculos", json=_PAYLOAD)

    # Assert
    assert resposta.status_code == 401
    assert resposta.json()["code"] == "TOKEN_INVALIDO"


@pytest.mark.unit
def test_listar_disponiveis_e_publico(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """Listagem de disponiveis nao exige token e retorna 200."""
    # Arrange
    caso = AsyncMock(spec=ListarDisponiveis)
    caso.executar.return_value = [construir_veiculo_dto()]
    monkeypatch.setattr(veiculos_controller, "ListarDisponiveis", lambda q: caso)

    # Act
    resposta = client.get(
        "/v1/veiculos?status=DISPONIVEL",
    )

    # Assert
    assert resposta.status_code == 200
    assert len(resposta.json()) == 1


@pytest.mark.unit
def test_listar_com_status_reservado_retorna_422(client: TestClient) -> None:
    """RESERVADO nao tem vitrine propria: a listagem so aceita DISPONIVEL/VENDIDO."""
    # Act
    resposta = client.get("/v1/veiculos?status=RESERVADO")

    # Assert
    assert resposta.status_code == 422
