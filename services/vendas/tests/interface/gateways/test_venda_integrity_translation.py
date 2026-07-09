"""Testes de traducao de IntegrityError para VeiculoIndisponivelError."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Venda
from src.domain.exceptions import VeiculoIndisponivelError
from src.domain.value_objects import Preco
from src.interface.gateways import VendaRepositoryGateway


@pytest.mark.unit
async def test_adicionar_com_integrity_error_levanta_veiculo_indisponivel() -> None:
    """Quando flush levanta IntegrityError, traducao para VeiculoIndisponivelError."""
    # Arrange
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock(side_effect=IntegrityError("INSERT", {}, Exception("duplicate key")))
    gateway = VendaRepositoryGateway(cast(AsyncSession, session))

    agora = datetime.now(UTC)
    venda_id = uuid4()
    veiculo_id = uuid4()
    venda = Venda(
        id=venda_id,
        veiculo_id=veiculo_id,
        cliente_id="sub-test",
        preco_venda=Preco(valor=Decimal("85000.00")),
        data_venda=agora,
        created_at=agora,
    )

    # Act / Assert
    with pytest.raises(VeiculoIndisponivelError) as exc_info:
        await gateway.adicionar(venda)

    assert exc_info.value.veiculo_id == veiculo_id
    session.add.assert_called_once()


@pytest.mark.unit
async def test_adicionar_com_sucesso_nao_levanta() -> None:
    """Quando flush nao levanta erro, adicionar completa sem excecao."""
    # Arrange
    session = MagicMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    gateway = VendaRepositoryGateway(cast(AsyncSession, session))

    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-test",
        preco_venda=Preco(valor=Decimal("85000.00")),
        data_venda=agora,
        created_at=agora,
    )

    # Act
    await gateway.adicionar(venda)

    # Assert
    session.add.assert_called_once()
    session.flush.assert_called_once()


@pytest.mark.unit
async def test_adicionar_session_add_chamado_antes_flush() -> None:
    """Session.add deve ser chamado antes de session.flush (ordem de operacoes)."""
    # Arrange
    session = MagicMock()
    add_call_order = []
    flush_call_order = []

    def track_add(*args, **kwargs):
        add_call_order.append("add")

    def track_flush(*args, **kwargs):
        flush_call_order.append("flush")
        return AsyncMock()

    session.add = MagicMock(side_effect=track_add)
    session.flush = AsyncMock(side_effect=track_flush)
    gateway = VendaRepositoryGateway(cast(AsyncSession, session))

    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-test",
        preco_venda=Preco(valor=Decimal("85000.00")),
        data_venda=agora,
        created_at=agora,
    )

    # Act
    await gateway.adicionar(venda)

    # Assert
    session.add.assert_called_once()
    session.flush.assert_called_once()
