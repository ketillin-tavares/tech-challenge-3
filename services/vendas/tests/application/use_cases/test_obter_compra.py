"""Testes unitarios do caso de uso ObterCompra."""

from uuid import uuid4

import pytest

from src.application.dtos import TransicaoCompraCommand
from src.application.use_cases.obter_compra import ObterCompra
from src.domain.exceptions import VendaNaoEncontradaError
from src.domain.value_objects import StatusVenda
from tests.application.conftest import (
    FakeUnitOfWork,
    FakeVeiculoRepository,
    FakeVendaRepository,
    construir_veiculo,
    construir_venda,
)


@pytest.mark.unit
async def test_obter_compra_sucesso() -> None:
    """Obter compra retorna recibo da venda do cliente."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo()
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    vendas.semear(venda)
    caso = ObterCompra(uow)

    # Act
    recibo = await caso.executar(
        TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-1", eh_admin=False)
    )

    # Assert
    assert recibo.id == venda.id
    assert recibo.veiculo_id == venda.veiculo_id
    assert recibo.cliente_id == "sub-cliente-1"
    assert recibo.status is StatusVenda.PENDENTE
    assert uow.commits == 0  # Apenas leitura


@pytest.mark.unit
async def test_obter_compra_venda_nao_encontrada() -> None:
    """Obter compra inexistente levanta VendaNaoEncontradaError."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    caso = ObterCompra(uow)

    # Act / Assert
    with pytest.raises(VendaNaoEncontradaError):
        await caso.executar(
            TransicaoCompraCommand(venda_id=uuid4(), cliente_id="sub-cliente-1", eh_admin=False)
        )


@pytest.mark.unit
async def test_obter_compra_cliente_errado_nao_admin() -> None:
    """Obter compra de outro cliente sem ser admin levanta VendaNaoEncontradaError."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo()
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    vendas.semear(venda)
    caso = ObterCompra(uow)

    # Act / Assert
    with pytest.raises(VendaNaoEncontradaError):
        await caso.executar(
            TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-cliente-2", eh_admin=False)
        )


@pytest.mark.unit
async def test_obter_compra_admin_acesso_qualquer_cliente() -> None:
    """Admin pode obter compra de qualquer cliente."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo()
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    vendas.semear(venda)
    caso = ObterCompra(uow)

    # Act
    recibo = await caso.executar(
        TransicaoCompraCommand(venda_id=venda.id, cliente_id="sub-admin", eh_admin=True)
    )

    # Assert
    assert recibo.id == venda.id
    assert recibo.cliente_id == "sub-cliente-1"
