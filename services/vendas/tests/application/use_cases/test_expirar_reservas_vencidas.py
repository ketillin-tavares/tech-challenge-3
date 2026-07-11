"""Testes unitarios do caso de uso ExpirarReservasVencidas."""

from datetime import UTC, datetime, timedelta

import pytest

from src.application.use_cases.expirar_reservas_vencidas import ExpirarReservasVencidas
from src.domain.value_objects import StatusVeiculo, StatusVenda
from tests.application.conftest import (
    FakeUnitOfWork,
    FakeVeiculoRepository,
    FakeVendaRepository,
    construir_veiculo,
    construir_venda,
)


@pytest.mark.unit
async def test_expirar_reservas_vencidas_cancela_e_libera() -> None:
    """ExpirarReservasVencidas cancela vendas expiradas e libera veiculos."""
    # Arrange
    agora = datetime.now(UTC)
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo1 = construir_veiculo(status=StatusVeiculo.RESERVADO)
    veiculo2 = construir_veiculo(status=StatusVeiculo.RESERVADO)
    veiculos.semear(veiculo1)
    veiculos.semear(veiculo2)
    venda1 = construir_venda(veiculo_id=veiculo1.id)
    venda1.expira_em = agora - timedelta(hours=1)  # Expirada
    venda2 = construir_venda(veiculo_id=veiculo2.id)
    venda2.expira_em = agora + timedelta(hours=1)  # Ainda válida
    vendas.semear(venda1)
    vendas.semear(venda2)
    caso = ExpirarReservasVencidas(uow, limite=100)

    # Act
    recibos = await caso.executar()

    # Assert
    assert len(recibos) == 1
    assert recibos[0].id == venda1.id
    assert recibos[0].status is StatusVenda.CANCELADA
    # Validar que venda1 foi cancelada e veiculo1 foi liberado
    assert vendas.atualizadas[0].status is StatusVenda.CANCELADA
    assert veiculos.atualizados[0].status is StatusVeiculo.DISPONIVEL
    assert uow.commits == 1


@pytest.mark.unit
async def test_expirar_reservas_vencidas_respeita_limite() -> None:
    """ExpirarReservasVencidas processa no máximo `limite` vendas."""
    # Arrange
    agora = datetime.now(UTC)
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    for _i in range(5):
        veiculo = construir_veiculo(status=StatusVeiculo.RESERVADO)
        veiculos.semear(veiculo)
        venda = construir_venda(veiculo_id=veiculo.id)
        venda.expira_em = agora - timedelta(hours=1)
        vendas.semear(venda)
    caso = ExpirarReservasVencidas(uow, limite=2)

    # Act
    recibos = await caso.executar()

    # Assert
    assert len(recibos) == 2
    assert len(vendas.atualizadas) == 2
    assert uow.commits == 1


@pytest.mark.unit
async def test_expirar_reservas_vencidas_vazio_nao_comita() -> None:
    """ExpirarReservasVencidas sem vendas expiradas não faz commit."""
    # Arrange
    agora = datetime.now(UTC)
    veiculos = FakeVeiculoRepository()
    vendas = FakeVendaRepository()
    uow = FakeUnitOfWork(veiculos, vendas)
    veiculo = construir_veiculo()
    veiculos.semear(veiculo)
    venda = construir_venda(veiculo_id=veiculo.id)
    venda.expira_em = agora + timedelta(hours=1)  # Ainda válida
    vendas.semear(venda)
    caso = ExpirarReservasVencidas(uow, limite=100)

    # Act
    recibos = await caso.executar()

    # Assert
    assert len(recibos) == 0
    assert uow.commits == 0  # Sem alterações, sem commit
