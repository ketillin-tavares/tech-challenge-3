"""Testes unitarios do caso de uso IniciarCompra."""

from datetime import timedelta
from uuid import uuid4

import pytest

from src.application.dtos import IniciarCompraCommand
from src.application.use_cases.iniciar_compra import IniciarCompra
from src.domain.exceptions import (
    ReservaAtivaExistenteError,
    VeiculoIndisponivelError,
    VeiculoNaoEncontradoError,
)
from src.domain.value_objects import StatusVeiculo, StatusVenda
from tests.application.conftest import (
    FakeUnitOfWork,
    FakeVeiculoRepository,
    FakeVendaRepository,
    construir_veiculo,
)


@pytest.mark.unit
async def test_iniciar_compra_disponivel_cria_reserva() -> None:
    """Inicia compra de veiculo DISPONIVEL cria venda PENDENTE e reserva."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(preco="85000.00")
    veiculos.semear(veiculo)
    caso = IniciarCompra(uow, reserva_ttl=timedelta(hours=1))

    # Act
    recibo = await caso.executar(
        IniciarCompraCommand(veiculo_id=veiculo.id, cliente_id="sub-cliente-1")
    )

    # Assert
    assert recibo.veiculo_id == veiculo.id
    assert recibo.cliente_id == "sub-cliente-1"
    assert recibo.preco_venda == veiculo.preco.valor
    assert recibo.status is StatusVenda.PENDENTE
    assert recibo.expira_em is not None
    assert recibo.data_venda is None
    assert veiculos.atualizados[0].status is StatusVeiculo.RESERVADO
    assert uow.commits == 1
    assert uow.rollbacks == 0
    assert len(vendas.adicionadas) == 1


@pytest.mark.unit
async def test_iniciar_compra_veiculo_inexistente_faz_rollback() -> None:
    """Iniciar compra de veiculo inexistente levanta erro e faz rollback."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    caso = IniciarCompra(uow, reserva_ttl=timedelta(hours=1))

    # Act / Assert
    with pytest.raises(VeiculoNaoEncontradoError):
        await caso.executar(IniciarCompraCommand(veiculo_id=uuid4(), cliente_id="sub-cliente-1"))
    assert uow.commits == 0
    assert uow.rollbacks == 1


@pytest.mark.unit
async def test_iniciar_compra_veiculo_indisponivel_faz_rollback() -> None:
    """Iniciar compra de veiculo nao DISPONIVEL levanta erro e faz rollback."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(status=StatusVeiculo.VENDIDO)
    veiculos.semear(veiculo)
    caso = IniciarCompra(uow, reserva_ttl=timedelta(hours=1))

    # Act / Assert
    with pytest.raises(VeiculoIndisponivelError):
        await caso.executar(IniciarCompraCommand(veiculo_id=veiculo.id, cliente_id="sub-cliente-1"))
    assert uow.commits == 0
    assert uow.rollbacks == 1


@pytest.mark.unit
async def test_iniciar_compra_cliente_ja_tem_reserva_ativa() -> None:
    """Iniciar compra quando ja tem venda PENDENTE levanta ReservaAtivaExistenteError."""
    # Arrange
    from tests.application.conftest import construir_venda

    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo()
    veiculos.semear(veiculo)
    venda_pendente = construir_venda(cliente_id="sub-cliente-1")
    vendas.semear(venda_pendente)
    caso = IniciarCompra(uow, reserva_ttl=timedelta(hours=1))

    # Act / Assert
    with pytest.raises(ReservaAtivaExistenteError):
        await caso.executar(IniciarCompraCommand(veiculo_id=veiculo.id, cliente_id="sub-cliente-1"))
    assert uow.commits == 0
    assert uow.rollbacks == 1


@pytest.mark.unit
async def test_iniciar_compra_clientes_diferentes_sem_conflito() -> None:
    """Dois clientes podem fazer compras sem conflito."""
    # Arrange
    from tests.application.conftest import construir_venda

    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo1 = construir_veiculo()
    veiculo2 = construir_veiculo()
    veiculos.semear(veiculo1)
    veiculos.semear(veiculo2)
    venda1 = construir_venda(cliente_id="sub-cliente-1", veiculo_id=veiculo1.id)
    vendas.semear(venda1)
    caso = IniciarCompra(uow, reserva_ttl=timedelta(hours=1))

    # Act
    recibo = await caso.executar(
        IniciarCompraCommand(veiculo_id=veiculo2.id, cliente_id="sub-cliente-2")
    )

    # Assert
    assert recibo.cliente_id == "sub-cliente-2"
    assert uow.commits == 1
