"""Testes unitarios do caso de uso EditarVeiculo (ports mockados via fakes)."""

from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.application.dtos import EditarVeiculoCommand
from src.application.use_cases.editar_veiculo import EditarVeiculo
from src.domain.exceptions import VeiculoNaoEncontradoError, VeiculoVendidoNaoEditavelError
from src.domain.value_objects import StatusVeiculo
from tests.application.conftest import FakeVeiculoRepository, construir_veiculo


def _comando(veiculo_id: UUID) -> EditarVeiculoCommand:
    """Monta um comando de edicao valido para um id."""
    return EditarVeiculoCommand(
        veiculo_id=veiculo_id,
        marca="Fiat",
        modelo="Pulse",
        ano=2024,
        cor="Vermelho",
        preco=Decimal("110000.00"),
    )


@pytest.mark.unit
async def test_editar_veiculo_inexistente_levanta_erro() -> None:
    """Editar um id inexistente resulta em VeiculoNaoEncontradoError."""
    # Arrange
    repositorio = FakeVeiculoRepository()
    caso = EditarVeiculo(repositorio)

    # Act / Assert
    with pytest.raises(VeiculoNaoEncontradoError):
        await caso.executar(_comando(uuid4()))


@pytest.mark.unit
async def test_editar_veiculo_disponivel_atualiza() -> None:
    """Edicao de veiculo DISPONIVEL substitui os campos e persiste."""
    # Arrange
    repositorio = FakeVeiculoRepository()
    veiculo = construir_veiculo(status=StatusVeiculo.DISPONIVEL)
    repositorio.semear(veiculo)
    caso = EditarVeiculo(repositorio)

    # Act
    dto = await caso.executar(_comando(veiculo.id))

    # Assert
    assert dto.marca == "Fiat"
    assert dto.preco == Decimal("110000.00")
    assert len(repositorio.atualizados) == 1


@pytest.mark.unit
async def test_editar_veiculo_vendido_levanta_erro() -> None:
    """Editar um veiculo VENDIDO e proibido."""
    # Arrange
    repositorio = FakeVeiculoRepository()
    veiculo = construir_veiculo(status=StatusVeiculo.VENDIDO)
    repositorio.semear(veiculo)
    caso = EditarVeiculo(repositorio)

    # Act / Assert
    with pytest.raises(VeiculoVendidoNaoEditavelError):
        await caso.executar(_comando(veiculo.id))
    assert repositorio.atualizados == []
