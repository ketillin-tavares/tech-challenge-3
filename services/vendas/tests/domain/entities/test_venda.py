"""Testes da entidade Venda (transicoes de estado, expiração)."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities import Venda
from src.domain.exceptions import TransicaoVendaInvalidaError
from src.domain.value_objects import Preco, StatusVenda


@pytest.mark.unit
def test_venda_nascente_e_pendente() -> None:
    """Venda criada é PENDENTE por padrão."""
    # Arrange
    agora = datetime.now(UTC)
    venda_id = uuid4()
    veiculo_id = uuid4()

    # Act
    venda = Venda(
        id=venda_id,
        veiculo_id=veiculo_id,
        cliente_id="sub-abc-123",
        preco_venda=Preco(valor=Decimal("85000.00")),
        expira_em=agora + timedelta(hours=1),
        created_at=agora,
        updated_at=agora,
    )

    # Assert
    assert venda.status is StatusVenda.PENDENTE
    assert venda.data_venda is None
    assert venda.expira_em is not None


@pytest.mark.unit
def test_venda_efetivar_pendente_para_paga() -> None:
    """Efetivar muda PENDENTE para PAGA e preenche data_venda."""
    # Arrange
    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-abc-123",
        preco_venda=Preco(valor=Decimal("85000.00")),
        expira_em=agora + timedelta(hours=1),
        created_at=agora,
        updated_at=agora,
    )

    # Act
    venda.efetivar(agora)

    # Assert
    assert venda.status is StatusVenda.PAGA
    assert venda.data_venda == agora
    assert venda.updated_at == agora


@pytest.mark.unit
def test_venda_efetivar_paga_invalido() -> None:
    """Efetivar venda PAGA levanta TransicaoVendaInvalidaError."""
    # Arrange
    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-abc-123",
        preco_venda=Preco(valor=Decimal("85000.00")),
        status=StatusVenda.PAGA,
        data_venda=agora,
        created_at=agora,
        updated_at=agora,
    )

    # Act / Assert
    with pytest.raises(TransicaoVendaInvalidaError):
        venda.efetivar(agora)


@pytest.mark.unit
def test_venda_cancelar_pendente_para_cancelada() -> None:
    """Cancelar muda PENDENTE para CANCELADA."""
    # Arrange
    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-abc-123",
        preco_venda=Preco(valor=Decimal("85000.00")),
        expira_em=agora + timedelta(hours=1),
        created_at=agora,
        updated_at=agora,
    )

    # Act
    venda.cancelar(agora)

    # Assert
    assert venda.status is StatusVenda.CANCELADA
    assert venda.data_venda is None
    assert venda.updated_at == agora


@pytest.mark.unit
def test_venda_cancelar_paga_invalido() -> None:
    """Cancelar venda PAGA levanta TransicaoVendaInvalidaError."""
    # Arrange
    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-abc-123",
        preco_venda=Preco(valor=Decimal("85000.00")),
        status=StatusVenda.PAGA,
        data_venda=agora,
        created_at=agora,
        updated_at=agora,
    )

    # Act / Assert
    with pytest.raises(TransicaoVendaInvalidaError):
        venda.cancelar(agora)


@pytest.mark.unit
def test_venda_esta_expirada_verdadeiro() -> None:
    """Venda PENDENTE com expira_em no passado é expirada."""
    # Arrange
    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-abc-123",
        preco_venda=Preco(valor=Decimal("85000.00")),
        status=StatusVenda.PENDENTE,
        expira_em=agora - timedelta(hours=1),
        created_at=agora,
        updated_at=agora,
    )

    # Act
    resultado = venda.esta_expirada(agora)

    # Assert
    assert resultado is True


@pytest.mark.unit
def test_venda_esta_expirada_falso_ainda_valida() -> None:
    """Venda PENDENTE com expira_em no futuro não é expirada."""
    # Arrange
    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-abc-123",
        preco_venda=Preco(valor=Decimal("85000.00")),
        status=StatusVenda.PENDENTE,
        expira_em=agora + timedelta(hours=1),
        created_at=agora,
        updated_at=agora,
    )

    # Act
    resultado = venda.esta_expirada(agora)

    # Assert
    assert resultado is False


@pytest.mark.unit
def test_venda_esta_expirada_falso_nao_pendente() -> None:
    """Venda PAGA nunca é expirada (mesmo com expira_em vencido)."""
    # Arrange
    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-abc-123",
        preco_venda=Preco(valor=Decimal("85000.00")),
        status=StatusVenda.PAGA,
        data_venda=agora,
        expira_em=agora - timedelta(hours=1),
        created_at=agora,
        updated_at=agora,
    )

    # Act
    resultado = venda.esta_expirada(agora)

    # Assert
    assert resultado is False
