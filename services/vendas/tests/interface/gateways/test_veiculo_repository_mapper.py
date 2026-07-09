"""Testes dos mappers da entidade Veiculo (entity <-> model conversions)."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities import Veiculo
from src.domain.value_objects import Ano, Preco, StatusVeiculo
from src.infrastructure.models import VeiculoModel
from src.interface.gateways import VeiculoRepositoryGateway


@pytest.mark.unit
def test_entity_to_model_converte_veiculo_em_veiculo_model() -> None:
    """Mapper _entity_to_model converte entidade Veiculo para VeiculoModel."""
    # Arrange
    agora = datetime.now(UTC)
    veiculo_id = uuid4()
    veiculo = Veiculo(
        id=veiculo_id,
        marca="Toyota",
        modelo="Corolla",
        ano=Ano(valor=2020),
        cor="Prata",
        preco=Preco(valor=Decimal("85000.00")),
        status=StatusVeiculo.DISPONIVEL,
        created_at=agora,
        updated_at=agora,
    )

    # Act
    model = VeiculoRepositoryGateway._entity_to_model(veiculo)

    # Assert
    assert model.id == veiculo_id
    assert model.marca == "Toyota"
    assert model.modelo == "Corolla"
    assert model.ano == 2020
    assert isinstance(model.ano, int)
    assert model.cor == "Prata"
    assert model.preco == Decimal("85000.00")
    assert isinstance(model.preco, Decimal)
    assert model.status == "DISPONIVEL"
    assert isinstance(model.status, str)
    assert model.created_at == agora
    assert model.updated_at == agora


@pytest.mark.unit
def test_model_to_entity_converte_veiculo_model_em_veiculo() -> None:
    """Mapper _model_to_entity converte VeiculoModel para entidade Veiculo."""
    # Arrange
    agora = datetime.now(UTC)
    veiculo_id = uuid4()
    model = VeiculoModel(
        id=veiculo_id,
        marca="Honda",
        modelo="Civic",
        ano=2022,
        cor="Preto",
        preco=Decimal("120000.00"),
        status="DISPONIVEL",
        created_at=agora,
        updated_at=agora,
    )

    # Act
    veiculo = VeiculoRepositoryGateway._model_to_entity(model)

    # Assert
    assert veiculo.id == veiculo_id
    assert veiculo.marca == "Honda"
    assert veiculo.modelo == "Civic"
    assert veiculo.ano.valor == 2022
    assert veiculo.cor == "Preto"
    assert veiculo.preco.valor == Decimal("120000.00")
    assert isinstance(veiculo.preco.valor, Decimal)
    assert veiculo.status is StatusVeiculo.DISPONIVEL
    assert veiculo.created_at == agora
    assert veiculo.updated_at == agora


@pytest.mark.unit
def test_round_trip_entity_to_model_to_entity_preserva_dados() -> None:
    """Round-trip entidade -> model -> entidade preserva todos os campos."""
    # Arrange
    agora = datetime.now(UTC)
    veiculo_id = uuid4()
    veiculo_original = Veiculo(
        id=veiculo_id,
        marca="Fiat",
        modelo="Pulse",
        ano=Ano(valor=2024),
        cor="Vermelho",
        preco=Preco(valor=Decimal("110000.50")),
        status=StatusVeiculo.VENDIDO,
        created_at=agora,
        updated_at=agora,
    )

    # Act
    model = VeiculoRepositoryGateway._entity_to_model(veiculo_original)
    veiculo_reconstruido = VeiculoRepositoryGateway._model_to_entity(model)

    # Assert
    assert veiculo_reconstruido.id == veiculo_original.id
    assert veiculo_reconstruido.marca == veiculo_original.marca
    assert veiculo_reconstruido.modelo == veiculo_original.modelo
    assert veiculo_reconstruido.ano == veiculo_original.ano
    assert veiculo_reconstruido.cor == veiculo_original.cor
    assert veiculo_reconstruido.preco == veiculo_original.preco
    assert veiculo_reconstruido.status == veiculo_original.status
    assert veiculo_reconstruido.created_at == veiculo_original.created_at
    assert veiculo_reconstruido.updated_at == veiculo_original.updated_at


@pytest.mark.unit
def test_entity_to_model_preserva_decimal_precision() -> None:
    """Decimal com duas casas decimais e preservado exatamente no round-trip."""
    # Arrange
    agora = datetime.now(UTC)
    veiculo = Veiculo(
        id=uuid4(),
        marca="Volks",
        modelo="Gol",
        ano=Ano(valor=2019),
        cor="Branco",
        preco=Preco(valor=Decimal("45999.99")),
        status=StatusVeiculo.DISPONIVEL,
        created_at=agora,
        updated_at=agora,
    )

    # Act
    model = VeiculoRepositoryGateway._entity_to_model(veiculo)

    # Assert
    assert model.preco == Decimal("45999.99")
    assert str(model.preco) == "45999.99"
