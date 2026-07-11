"""Testes do router de compras (TestClient + dependency_overrides)."""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.application.dtos import ReciboVendaDTO
from src.application.use_cases.iniciar_compra import IniciarCompra
from src.domain.exceptions import (
    ReservaAtivaExistenteError,
    ReservaExpiradaError,
    TransicaoVendaInvalidaError,
    VeiculoIndisponivelError,
    VendaNaoEncontradaError,
)
from src.domain.value_objects import StatusVenda
from src.interface.controllers.dependencies import get_token_verifier
from src.interface.controllers.v1 import compras_controller
from tests.interface.conftest import FakeTokenVerifier

_AUTH = {"Authorization": "Bearer token-de-teste"}


def _construir_recibo_dto() -> ReciboVendaDTO:
    """Cria um ReciboVendaDTO válido para testes."""
    agora = datetime.now(UTC)
    return ReciboVendaDTO(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="cliente-1",
        preco_venda=Decimal("85000.00"),
        status=StatusVenda.PENDENTE,
        expira_em=agora,
        data_venda=None,
    )


@pytest.mark.unit
def test_iniciar_compra_autenticado_retorna_201(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """Cliente autenticado inicia compra de veiculo (201) com recibo."""
    # Arrange
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    recibo = _construir_recibo_dto()
    caso = AsyncMock(spec=IniciarCompra)
    caso.executar.return_value = recibo
    monkeypatch.setattr(compras_controller, "IniciarCompra", lambda uow, reserva_ttl: caso)

    # Act
    resposta = client.post("/v1/compras", json={"veiculo_id": str(uuid4())}, headers=_AUTH)

    # Assert
    assert resposta.status_code == 201
    assert resposta.json()["status"] == "PENDENTE"
    assert resposta.json()["cliente_id"] == "cliente-1"


@pytest.mark.unit
def test_iniciar_compra_sem_token_retorna_401(app: FastAPI, client: TestClient) -> None:
    """Compra sem token recebe 401."""
    # Act
    resposta = client.post("/v1/compras", json={"veiculo_id": str(uuid4())})

    # Assert
    assert resposta.status_code == 401


@pytest.mark.unit
def test_iniciar_compra_veiculo_indisponivel_retorna_409(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """Iniciar compra de veiculo indisponivel resulta em 409."""
    # Arrange
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    caso = AsyncMock(spec=IniciarCompra)
    caso.executar.side_effect = VeiculoIndisponivelError(uuid4())
    monkeypatch.setattr(compras_controller, "IniciarCompra", lambda uow, reserva_ttl: caso)

    # Act
    resposta = client.post("/v1/compras", json={"veiculo_id": str(uuid4())}, headers=_AUTH)

    # Assert
    assert resposta.status_code == 409


@pytest.mark.unit
def test_iniciar_compra_reserva_ativa_existente_retorna_409(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """Iniciar compra com reserva ativa existente resulta em 409."""
    # Arrange
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    caso = AsyncMock(spec=IniciarCompra)
    caso.executar.side_effect = ReservaAtivaExistenteError()
    monkeypatch.setattr(compras_controller, "IniciarCompra", lambda uow, reserva_ttl: caso)

    # Act
    resposta = client.post("/v1/compras", json={"veiculo_id": str(uuid4())}, headers=_AUTH)

    # Assert
    assert resposta.status_code == 409


@pytest.mark.unit
def test_efetivar_compra_retorna_200(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """Efetivar compra retorna 200 com recibo PAGA."""
    # Arrange
    venda_id = uuid4()
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    recibo = _construir_recibo_dto()
    recibo.status = StatusVenda.PAGA
    recibo.data_venda = datetime.now(UTC)
    caso = AsyncMock()
    caso.executar.return_value = recibo
    monkeypatch.setattr(compras_controller, "EfetivarCompra", lambda uow: caso)

    # Act
    resposta = client.post(f"/v1/compras/{venda_id}/efetivacao", headers=_AUTH)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "PAGA"


@pytest.mark.unit
def test_efetivar_compra_nao_encontrada_retorna_404(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """Efetivar venda inexistente retorna 404."""
    # Arrange
    venda_id = uuid4()
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    caso = AsyncMock()
    caso.executar.side_effect = VendaNaoEncontradaError(venda_id)
    monkeypatch.setattr(compras_controller, "EfetivarCompra", lambda uow: caso)

    # Act
    resposta = client.post(f"/v1/compras/{venda_id}/efetivacao", headers=_AUTH)

    # Assert
    assert resposta.status_code == 404


@pytest.mark.unit
def test_efetivar_compra_expirada_retorna_409(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """Efetivar compra expirada retorna 409."""
    # Arrange
    venda_id = uuid4()
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    caso = AsyncMock()
    caso.executar.side_effect = ReservaExpiradaError(venda_id)
    monkeypatch.setattr(compras_controller, "EfetivarCompra", lambda uow: caso)

    # Act
    resposta = client.post(f"/v1/compras/{venda_id}/efetivacao", headers=_AUTH)

    # Assert
    assert resposta.status_code == 409


@pytest.mark.unit
def test_cancelar_compra_retorna_200(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """Cancelar compra retorna 200 com recibo CANCELADA."""
    # Arrange
    venda_id = uuid4()
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    recibo = _construir_recibo_dto()
    recibo.status = StatusVenda.CANCELADA
    caso = AsyncMock()
    caso.executar.return_value = recibo
    monkeypatch.setattr(compras_controller, "CancelarCompra", lambda uow: caso)

    # Act
    resposta = client.post(f"/v1/compras/{venda_id}/cancelamento", headers=_AUTH)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "CANCELADA"


@pytest.mark.unit
def test_cancelar_compra_transicao_invalida_retorna_409(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """Cancelar compra PAGA retorna 409."""
    # Arrange
    venda_id = uuid4()
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    caso = AsyncMock()
    caso.executar.side_effect = TransicaoVendaInvalidaError(venda_id)
    monkeypatch.setattr(compras_controller, "CancelarCompra", lambda uow: caso)

    # Act
    resposta = client.post(f"/v1/compras/{venda_id}/cancelamento", headers=_AUTH)

    # Assert
    assert resposta.status_code == 409


@pytest.mark.unit
def test_obter_compra_retorna_200(app: FastAPI, client: TestClient, monkeypatch) -> None:
    """Obter compra retorna 200 com recibo."""
    # Arrange
    venda_id = uuid4()
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    recibo = _construir_recibo_dto()
    caso = AsyncMock()
    caso.executar.return_value = recibo
    monkeypatch.setattr(compras_controller, "ObterCompra", lambda uow: caso)

    # Act
    resposta = client.get(f"/v1/compras/{venda_id}", headers=_AUTH)

    # Assert
    assert resposta.status_code == 200
    assert resposta.json()["id"] == str(recibo.id)


@pytest.mark.unit
def test_obter_compra_nao_encontrada_retorna_404(
    app: FastAPI, client: TestClient, monkeypatch
) -> None:
    """Obter venda inexistente retorna 404."""
    # Arrange
    venda_id = uuid4()
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(sub="cliente-1")
    caso = AsyncMock()
    caso.executar.side_effect = VendaNaoEncontradaError(venda_id)
    monkeypatch.setattr(compras_controller, "ObterCompra", lambda uow: caso)

    # Act
    resposta = client.get(f"/v1/compras/{venda_id}", headers=_AUTH)

    # Assert
    assert resposta.status_code == 404
