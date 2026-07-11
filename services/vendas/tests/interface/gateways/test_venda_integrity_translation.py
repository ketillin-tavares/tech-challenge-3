"""Testes de traducao de IntegrityError para excecoes de dominio."""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import cast
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Venda
from src.domain.exceptions import ReservaAtivaExistenteError, VeiculoIndisponivelError
from src.domain.value_objects import Preco, StatusVenda
from src.interface.gateways import VendaRepositoryGateway


@pytest.mark.unit
async def test_adicionar_com_integrity_error_veiculo_levanta_veiculo_indisponivel() -> None:
    """IntegrityError com constraint de veiculo traduz para VeiculoIndisponivelError."""
    # Arrange
    session = MagicMock()
    session.add = MagicMock()
    erro_orig = Exception("duplicate key")
    erro = IntegrityError("INSERT", {}, erro_orig)
    session.flush = AsyncMock(side_effect=erro)
    gateway = VendaRepositoryGateway(cast(AsyncSession, session))

    agora = datetime.now(UTC)
    venda_id = uuid4()
    veiculo_id = uuid4()
    venda = Venda(
        id=venda_id,
        veiculo_id=veiculo_id,
        cliente_id="sub-test",
        preco_venda=Preco(valor=Decimal("85000.00")),
        status=StatusVenda.PENDENTE,
        expira_em=agora + timedelta(hours=1),
        created_at=agora,
        updated_at=agora,
    )

    # Act / Assert
    with pytest.raises(VeiculoIndisponivelError) as exc_info:
        await gateway.adicionar(venda)

    assert exc_info.value.veiculo_id == veiculo_id
    session.add.assert_called_once()


@pytest.mark.unit
async def test_adicionar_com_integrity_error_cliente_levanta_reserva_ativa() -> None:
    """IntegrityError com constraint de cliente traduz para ReservaAtivaExistenteError."""
    # Arrange
    session = MagicMock()
    session.add = MagicMock()
    erro_orig = Exception("uq_vendas_cliente_pendente")
    erro = IntegrityError("INSERT", {}, erro_orig)
    session.flush = AsyncMock(side_effect=erro)
    gateway = VendaRepositoryGateway(cast(AsyncSession, session))

    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=uuid4(),
        cliente_id="sub-test",
        preco_venda=Preco(valor=Decimal("85000.00")),
        status=StatusVenda.PENDENTE,
        expira_em=agora + timedelta(hours=1),
        created_at=agora,
        updated_at=agora,
    )

    # Act / Assert
    with pytest.raises(ReservaAtivaExistenteError):
        await gateway.adicionar(venda)

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
        status=StatusVenda.PENDENTE,
        expira_em=agora + timedelta(hours=1),
        created_at=agora,
        updated_at=agora,
    )

    # Act
    await gateway.adicionar(venda)

    # Assert
    session.add.assert_called_once()
    session.flush.assert_called_once()
