"""Testes unitarios do caso de uso EfetivarCompra."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from src.application.dtos import TransicaoCompraCommand
from src.application.use_cases.efetivar_compra import EfetivarCompra
from src.domain.exceptions import (
    ReservaExpiradaError,
    TransicaoVendaInvalidaError,
    VendaNaoEncontradaError,
)
from src.domain.value_objects import StatusVeiculo, StatusVenda
from tests.application.conftest import (
    FakeUnitOfWork,
    FakeVeiculoRepository,
    FakeVendaRepository,
    construir_veiculo,
    construir_venda,
)


@pytest.mark.unit
async def test_efetivar_compra_pendente_sucesso() -> None:
    """Efetivar venda PENDENTE transita para PAGA e marca veiculo como VENDIDO."""
    # Arrange
    datetime.now(UTC)
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(status=StatusVeiculo.RESERVADO)
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    vendas.semear(venda)
    caso = EfetivarCompra(uow)

    # Act
    recibo = await caso.executar(
        TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-1", eh_admin=False)
    )

    # Assert
    assert recibo.status is StatusVenda.PAGA
    assert recibo.data_venda is not None
    assert veiculos.atualizados[0].status is StatusVeiculo.VENDIDO
    assert uow.commits == 1


@pytest.mark.unit
async def test_efetivar_compra_paga_idempotente() -> None:
    """Efetivar venda já PAGA retorna recibo sem alterar."""
    # Arrange
    agora = datetime.now(UTC)
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(status=StatusVeiculo.VENDIDO)
    veiculos.semear(veiculo)
    venda = construir_venda(
        veiculo_id=veiculo.id,
        cliente_id="sub-cliente-1",
    )
    venda.status = StatusVenda.PAGA
    venda.data_venda = agora
    vendas.semear(venda)
    caso = EfetivarCompra(uow)

    # Act
    recibo = await caso.executar(
        TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-1", eh_admin=False)
    )

    # Assert
    assert recibo.status is StatusVenda.PAGA
    assert len(vendas.atualizadas) == 0  # Sem alterações
    assert uow.commits == 0  # Sem commit


@pytest.mark.unit
async def test_efetivar_compra_cancelada_invalido() -> None:
    """Efetivar venda CANCELADA levanta TransicaoVendaInvalidaError."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo()
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    venda.status = StatusVenda.CANCELADA
    vendas.semear(venda)
    caso = EfetivarCompra(uow)

    # Act / Assert
    with pytest.raises(TransicaoVendaInvalidaError):
        await caso.executar(
            TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-1", eh_admin=False)
        )
    assert uow.rollbacks == 1


@pytest.mark.unit
async def test_efetivar_compra_expirada_cancela_e_libera() -> None:
    """Efetivar reserva expirada cancela venda, libera veiculo e levanta erro."""
    # Arrange
    agora = datetime.now(UTC)
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(status=StatusVeiculo.RESERVADO)
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    venda.expira_em = agora - timedelta(hours=1)  # Expirada
    vendas.semear(venda)
    caso = EfetivarCompra(uow)

    # Act / Assert
    with pytest.raises(ReservaExpiradaError):
        await caso.executar(
            TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-1", eh_admin=False)
        )
    # Checagem de que cancelamento foi feito e commited
    assert vendas.atualizadas[0].status is StatusVenda.CANCELADA
    assert veiculos.atualizados[0].status is StatusVeiculo.DISPONIVEL
    assert uow.commits == 1  # Um commit pelo cancelamento da expiração


@pytest.mark.unit
async def test_efetivar_compra_venda_nao_encontrada() -> None:
    """Efetivar venda inexistente levanta VendaNaoEncontradaError."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    caso = EfetivarCompra(uow)

    # Act / Assert
    with pytest.raises(VendaNaoEncontradaError):
        await caso.executar(
            TransicaoCompraCommand(venda_id=uuid4(), cliente_id="sub-cliente-1", eh_admin=False)
        )


@pytest.mark.unit
async def test_efetivar_compra_cliente_errado_nao_admin() -> None:
    """Efetivar venda de outro cliente sem ser admin levanta VendaNaoEncontradaError."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo()
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    vendas.semear(venda)
    caso = EfetivarCompra(uow)

    # Act / Assert
    with pytest.raises(VendaNaoEncontradaError):
        await caso.executar(
            TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-2", eh_admin=False)
        )


@pytest.mark.unit
async def test_efetivar_compra_cliente_errado_admin_permitido() -> None:
    """Admin pode efetivar compra de qualquer cliente."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(status=StatusVeiculo.RESERVADO)
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    vendas.semear(venda)
    caso = EfetivarCompra(uow)

    # Act
    recibo = await caso.executar(
        TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-admin", eh_admin=True)
    )

    # Assert
    assert recibo.status is StatusVenda.PAGA
    assert uow.commits == 1
