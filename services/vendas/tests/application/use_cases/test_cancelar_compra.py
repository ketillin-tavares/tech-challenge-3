"""Testes unitarios do caso de uso CancelarCompra."""

from uuid import uuid4

import pytest

from src.application.dtos import TransicaoCompraCommand
from src.application.use_cases.cancelar_compra import CancelarCompra
from src.domain.exceptions import (
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
async def test_cancelar_compra_pendente_sucesso() -> None:
    """Cancelar venda PENDENTE transita para CANCELADA e libera veiculo."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(status=StatusVeiculo.RESERVADO)
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    vendas.semear(venda)
    caso = CancelarCompra(uow)

    # Act
    recibo = await caso.executar(
        TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-1", eh_admin=False)
    )

    # Assert
    assert recibo.status is StatusVenda.CANCELADA
    assert veiculos.atualizados[0].status is StatusVeiculo.DISPONIVEL
    assert uow.commits == 1


@pytest.mark.unit
async def test_cancelar_compra_cancelada_idempotente() -> None:
    """Cancelar venda já CANCELADA retorna recibo sem alterar."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(status=StatusVeiculo.DISPONIVEL)
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    venda.status = StatusVenda.CANCELADA
    vendas.semear(venda)
    caso = CancelarCompra(uow)

    # Act
    recibo = await caso.executar(
        TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-1", eh_admin=False)
    )

    # Assert
    assert recibo.status is StatusVenda.CANCELADA
    assert len(vendas.atualizadas) == 0  # Sem alterações
    assert uow.commits == 0


@pytest.mark.unit
async def test_cancelar_compra_paga_invalido() -> None:
    """Cancelar venda PAGA levanta TransicaoVendaInvalidaError."""
    # Arrange
    from datetime import UTC, datetime

    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(status=StatusVeiculo.VENDIDO)
    veiculos.semear(veiculo)
    agora = datetime.now(UTC)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    venda.status = StatusVenda.PAGA
    venda.data_venda = agora
    vendas.semear(venda)
    caso = CancelarCompra(uow)

    # Act / Assert
    with pytest.raises(TransicaoVendaInvalidaError):
        await caso.executar(
            TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-1", eh_admin=False)
        )
    assert uow.rollbacks == 1


@pytest.mark.unit
async def test_cancelar_compra_venda_nao_encontrada() -> None:
    """Cancelar venda inexistente levanta VendaNaoEncontradaError."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    caso = CancelarCompra(uow)

    # Act / Assert
    with pytest.raises(VendaNaoEncontradaError):
        await caso.executar(
            TransicaoCompraCommand(venda_id=uuid4(), cliente_id="sub-cliente-1", eh_admin=False)
        )


@pytest.mark.unit
async def test_cancelar_compra_cliente_errado_nao_admin() -> None:
    """Cancelar venda de outro cliente sem ser admin levanta VendaNaoEncontradaError."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo()
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    vendas.semear(venda)
    caso = CancelarCompra(uow)

    # Act / Assert
    with pytest.raises(VendaNaoEncontradaError):
        await caso.executar(
            TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-2", eh_admin=False)
        )


@pytest.mark.unit
async def test_cancelar_compra_admin_pode_qualquer_cliente() -> None:
    """Admin pode cancelar compra de qualquer cliente."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(status=StatusVeiculo.RESERVADO)
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    vendas.semear(venda)
    caso = CancelarCompra(uow)

    # Act
    recibo = await caso.executar(
        TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-admin", eh_admin=True)
    )

    # Assert
    assert recibo.status is StatusVenda.CANCELADA
    assert uow.commits == 1
