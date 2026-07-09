"""Testes dos handlers globais de erro (mapeamento dominio/validacao -> HTTP)."""

from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from src.application.dtos.paginacao import PaginacaoQuery
from src.application.use_cases.cadastrar_veiculo import CadastrarVeiculo
from src.application.use_cases.editar_veiculo import EditarVeiculo
from src.domain.exceptions import VeiculoNaoEncontradoError
from src.interface.controllers.dependencies import get_token_verifier
from src.interface.controllers.v1 import veiculos_controller
from tests.interface.conftest import FakeTokenVerifier

_PAYLOAD = {
    "marca": "Toyota",
    "modelo": "Corolla",
    "ano": 2020,
    "cor": "Prata",
    "preco": "85000.00",
}
_AUTH = {"Authorization": "Bearer token-de-teste"}


def _erro_de_validacao() -> ValidationError:
    """Produz uma ValidationError real (como a de construcao de VO)."""
    try:
        PaginacaoQuery(limit=0)
    except ValidationError as exc:
        return exc
    raise AssertionError("PaginacaoQuery(limit=0) deveria falhar")


@pytest.mark.unit
def test_validation_error_de_use_case_retorna_422(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """ValidationError levantada no use case e mapeada para 422."""
    # Arrange
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(grupos=("admin",))
    caso = AsyncMock(spec=CadastrarVeiculo)
    caso.executar.side_effect = _erro_de_validacao()
    monkeypatch.setattr(veiculos_controller, "CadastrarVeiculo", lambda repo: caso)

    # Act
    resposta = client.post("/v1/veiculos", json=_PAYLOAD, headers=_AUTH)

    # Assert
    assert resposta.status_code == 422
    assert resposta.json()["code"] == "VALIDACAO"


@pytest.mark.unit
def test_veiculo_nao_encontrado_retorna_404(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """VeiculoNaoEncontradoError e mapeada para 404."""
    # Arrange
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(grupos=("admin",))
    caso = AsyncMock(spec=EditarVeiculo)
    caso.executar.side_effect = VeiculoNaoEncontradoError(uuid4())
    monkeypatch.setattr(veiculos_controller, "EditarVeiculo", lambda repo: caso)

    # Act
    resposta = client.put(f"/v1/veiculos/{uuid4()}", json=_PAYLOAD, headers=_AUTH)

    # Assert
    assert resposta.status_code == 404
    assert resposta.json()["code"] == "VEICULO_NAO_ENCONTRADO"
