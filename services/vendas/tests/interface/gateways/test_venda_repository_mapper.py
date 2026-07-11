"""Testes dos mappers da entidade Venda (entity <-> model conversions)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities import Venda
from src.domain.value_objects import Preco, StatusVenda
from src.infrastructure.models import VendaModel
from src.interface.gateways import VendaRepositoryGateway


@pytest.mark.unit
def test_entity_to_model_converte_venda_pendente_em_venda_model() -> None:
    """Mapper _entity_to_model converte entidade Venda PENDENTE para VendaModel."""
    # Arrange
    agora = datetime.now(UTC)
    venda_id = uuid4()
    veiculo_id = uuid4()
    venda = Venda(
        id=venda_id,
        veiculo_id=veiculo_id,
        cliente_id="sub-123-abc",
        preco_venda=Preco(valor=Decimal("85000.00")),
        status=StatusVenda.PENDENTE,
        expira_em=agora + timedelta(hours=1),
        data_venda=None,
        created_at=agora,
        updated_at=agora,
    )

    # Act
    model = VendaRepositoryGateway._entity_to_model(venda)

    # Assert
    assert model.id == venda_id
    assert model.veiculo_id == veiculo_id
    assert model.cliente_id == "sub-123-abc"
    assert model.preco_venda == Decimal("85000.00")
    assert model.status == "PENDENTE"
    assert model.expira_em == venda.expira_em
    assert model.data_venda is None
    assert model.created_at == agora
    assert model.updated_at == agora


@pytest.mark.unit
def test_model_to_entity_converte_venda_model_paga_em_venda() -> None:
    """Mapper _model_to_entity converte VendaModel PAGA para entidade Venda."""
    # Arrange
    agora = datetime.now(UTC)
    venda_id = uuid4()
    veiculo_id = uuid4()
    model = VendaModel(
        id=venda_id,
        veiculo_id=veiculo_id,
        cliente_id="sub-456-def",
        preco_venda=Decimal("120000.50"),
        status="PAGA",
        data_venda=agora,
        expira_em=None,
        created_at=agora,
        updated_at=agora,
    )

    # Act
    venda = VendaRepositoryGateway._model_to_entity(model)

    # Assert
    assert venda.id == venda_id
    assert venda.veiculo_id == veiculo_id
    assert venda.cliente_id == "sub-456-def"
    assert venda.preco_venda.valor == Decimal("120000.50")
    assert venda.status is StatusVenda.PAGA
    assert venda.data_venda == agora
    assert venda.created_at == agora
    assert venda.updated_at == agora


@pytest.mark.unit
def test_round_trip_entity_to_model_to_entity_preserva_dados() -> None:
    """Round-trip entidade -> model -> entidade preserva todos os campos."""
    # Arrange
    agora = datetime.now(UTC)
    expira_em = agora + timedelta(hours=1)
    venda_id = uuid4()
    veiculo_id = uuid4()
    venda_original = Venda(
        id=venda_id,
        veiculo_id=veiculo_id,
        cliente_id="sub-789-xyz",
        preco_venda=Preco(valor=Decimal("99999.99")),
        status=StatusVenda.PENDENTE,
        expira_em=expira_em,
        data_venda=None,
        created_at=agora,
        updated_at=agora,
    )

    # Act
    model = VendaRepositoryGateway._entity_to_model(venda_original)
    venda_reconstruida = VendaRepositoryGateway._model_to_entity(model)

    # Assert
    assert venda_reconstruida.id == venda_original.id
    assert venda_reconstruida.veiculo_id == venda_original.veiculo_id
    assert venda_reconstruida.cliente_id == venda_original.cliente_id
    assert venda_reconstruida.preco_venda == venda_original.preco_venda
    assert venda_reconstruida.status == venda_original.status
    assert venda_reconstruida.expira_em == venda_original.expira_em
    assert venda_reconstruida.data_venda == venda_original.data_venda
    assert venda_reconstruida.created_at == venda_original.created_at
    assert venda_reconstruida.updated_at == venda_original.updated_at


@pytest.mark.unit
def test_entity_to_model_preserva_decimal_precision() -> None:
    """Decimal com duas casas decimais e preservado exatamente no round-trip."""
    # Arrange
    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-111-222",
        preco_venda=Preco(valor=Decimal("45999.99")),
        status=StatusVenda.PENDENTE,
        expira_em=agora + timedelta(hours=1),
        data_venda=None,
        created_at=agora,
        updated_at=agora,
    )

    # Act
    model = VendaRepositoryGateway._entity_to_model(venda)

    # Assert
    assert model.preco_venda == Decimal("45999.99")
    assert str(model.preco_venda) == "45999.99"
