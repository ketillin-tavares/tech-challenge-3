"""Testes do router de compras (TestClient + dependency_overrides)."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.application.use_cases.comprar_veiculo import ComprarVeiculo
from src.domain.exceptions import VeiculoIndisponivelError
from src.interface.controllers.dependencies import get_token_verifier
from src.interface.controllers.v1 import compras_controller
from tests.interface.conftest import FakeTokenVerifier, construir_recibo_dto

_AUTH = {"Authorization": "Bearer token-de-teste"}


@pytest.mark.unit
def test_comprar_autenticado_retorna_201(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """Cliente autenticado compra um veiculo (201) com recibo."""
    # Arrange
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    recibo = construir_recibo_dto()
    caso = AsyncMock(spec=ComprarVeiculo)
    caso.executar.return_value = recibo
    monkeypatch.setattr(compras_controller, "ComprarVeiculo", lambda uow: caso)

    # Act
    resposta = client.post("/v1/compras", json={"veiculo_id": str(uuid4())}, headers=_AUTH)

    # Assert
    assert resposta.status_code == 201
    assert resposta.json()["cliente_id"] == "cliente-1"


@pytest.mark.unit
def test_comprar_sem_token_retorna_401(app: FastAPI, client: TestClient) -> None:
    """Compra sem token recebe 401."""
    # Act
    resposta = client.post("/v1/compras", json={"veiculo_id": str(uuid4())})

    # Assert
    assert resposta.status_code == 401


@pytest.mark.unit
def test_comprar_veiculo_indisponivel_retorna_409(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """Veiculo ja vendido resulta em 409 (mapeado do dominio)."""
    # Arrange
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    caso = AsyncMock(spec=ComprarVeiculo)
    caso.executar.side_effect = VeiculoIndisponivelError(uuid4())
    monkeypatch.setattr(compras_controller, "ComprarVeiculo", lambda uow: caso)

    # Act
    resposta = client.post("/v1/compras", json={"veiculo_id": str(uuid4())}, headers=_AUTH)

    # Assert
    assert resposta.status_code == 409
    assert resposta.json()["code"] == "VEICULO_INDISPONIVEL"
