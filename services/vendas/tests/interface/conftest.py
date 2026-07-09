"""Fixtures e dubles compartilhados dos testes de adapters (API HTTP)."""

from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.application.dtos import ReciboVendaDTO, VeiculoDTO, VeiculoVendidoDTO
from src.application.ports.token_verifier import TokenVerifier
from src.domain.value_objects import ClienteAutenticado, StatusVeiculo


class FakeTokenVerifier(TokenVerifier):
    """Verificador de token fake: devolve uma identidade pre-definida."""

    def __init__(self, sub: str = "cliente-1", grupos: tuple[str, ...] = ()) -> None:
        self._cliente = ClienteAutenticado(sub=sub, grupos=grupos)

    def verificar(self, token: str) -> ClienteAutenticado:
        return self._cliente


def construir_veiculo_dto(status: StatusVeiculo = StatusVeiculo.DISPONIVEL) -> VeiculoDTO:
    """Cria um VeiculoDTO valido para os testes."""
    agora = datetime.now(UTC)
    return VeiculoDTO(
        id=uuid4(),
        marca="Toyota",
        modelo="Corolla",
        ano=2020,
        cor="Prata",
        preco=Decimal("85000.00"),
        status=status,
        created_at=agora,
        updated_at=agora,
    )


def construir_veiculo_vendido_dto() -> VeiculoVendidoDTO:
    """Cria um VeiculoVendidoDTO valido para os testes."""
    agora = datetime.now(UTC)
    return VeiculoVendidoDTO(
        id=uuid4(),
        marca="Honda",
        modelo="Civic",
        ano=2021,
        cor="Preto",
        preco=Decimal("120000.00"),
        status=StatusVeiculo.VENDIDO,
        created_at=agora,
        updated_at=agora,
        preco_venda=Decimal("120000.00"),
        data_venda=agora,
    )


def construir_recibo_dto() -> ReciboVendaDTO:
    """Cria um ReciboVendaDTO valido para os testes."""
    agora = datetime.now(UTC)
    return ReciboVendaDTO(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="cliente-1",
        preco_venda=Decimal("85000.00"),
        data_venda=agora,
    )


@pytest.fixture
def app() -> FastAPI:
    """Fornece uma instancia fresca da aplicacao por teste."""
    from src.main import create_app

    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Fornece um TestClient sobre a aplicacao."""
    with TestClient(app) as test_client:
        yield test_client
