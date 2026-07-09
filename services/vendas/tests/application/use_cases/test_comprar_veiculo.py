"""Testes unitarios do caso de uso ComprarVeiculo (UnitOfWork fake)."""

from uuid import uuid4

import pytest

from src.application.dtos import ComprarVeiculoCommand
from src.application.use_cases.comprar_veiculo import ComprarVeiculo
from src.domain.exceptions import VeiculoIndisponivelError, VeiculoNaoEncontradoError
from src.domain.value_objects import StatusVeiculo
from tests.application.conftest import (
    FakeUnitOfWork,
    FakeVeiculoRepository,
    FakeVendaRepository,
    construir_veiculo,
)


@pytest.mark.unit
async def test_comprar_veiculo_disponivel_efetiva_venda_atomica() -> None:
    """Compra de veiculo DISPONIVEL registra a venda e comita uma vez."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(preco="85000.00")
    veiculos.semear(veiculo)
    caso = ComprarVeiculo(uow)

    # Act
    recibo = await caso.executar(ComprarVeiculoCommand(veiculo_id=veiculo.id, cliente_id="sub-abc"))

    # Assert
    assert recibo.veiculo_id == veiculo.id
    assert recibo.cliente_id == "sub-abc"
    assert recibo.preco_venda == veiculo.preco.valor
    assert veiculos.atualizados[0].status is StatusVeiculo.VENDIDO
    assert uow.commits == 1
    assert uow.rollbacks == 0
    assert len(vendas.adicionadas) == 1
    assert len(veiculos.atualizados) == 1


@pytest.mark.unit
async def test_comprar_veiculo_inexistente_faz_rollback() -> None:
    """Comprar id inexistente levanta erro e dispara rollback sem commit."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    caso = ComprarVeiculo(uow)

    # Act / Assert
    with pytest.raises(VeiculoNaoEncontradoError):
        await caso.executar(ComprarVeiculoCommand(veiculo_id=uuid4(), cliente_id="sub-abc"))
    assert uow.commits == 0
    assert uow.rollbacks == 1
    assert vendas.adicionadas == []


@pytest.mark.unit
async def test_comprar_veiculo_ja_vendido_faz_rollback() -> None:
    """Veiculo VENDIDO em memoria viola a transicao e dispara rollback."""
    # Arrange
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo(status=StatusVeiculo.VENDIDO)
    veiculos.semear(veiculo)
    caso = ComprarVeiculo(uow)

    # Act / Assert
    with pytest.raises(VeiculoIndisponivelError):
        await caso.executar(ComprarVeiculoCommand(veiculo_id=veiculo.id, cliente_id="sub-abc"))
    assert uow.commits == 0
    assert uow.rollbacks == 1
    assert vendas.adicionadas == []


@pytest.mark.unit
async def test_comprar_veiculo_violacao_de_unicidade_faz_rollback() -> None:
    """Corrida de dupla compra (UNIQUE) e traduzida e dispara rollback."""
    # Arrange
    veiculo = construir_veiculo()
    veiculos = FakeVeiculoRepository()
    veiculos.semear(veiculo)
    vendas = FakeVendaRepository(erro_ao_adicionar=VeiculoIndisponivelError(veiculo.id))
    uow = FakeUnitOfWork(veiculos, vendas)
    caso = ComprarVeiculo(uow)

    # Act / Assert
    with pytest.raises(VeiculoIndisponivelError):
        await caso.executar(ComprarVeiculoCommand(veiculo_id=veiculo.id, cliente_id="sub-abc"))
    assert uow.commits == 0
    assert uow.rollbacks == 1
