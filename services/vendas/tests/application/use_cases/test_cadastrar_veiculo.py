"""Testes unitarios do caso de uso CadastrarVeiculo (ports mockados via fakes)."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.application.dtos import CadastrarVeiculoCommand
from src.application.use_cases.cadastrar_veiculo import CadastrarVeiculo
from src.domain.value_objects import StatusVeiculo
from tests.application.conftest import FakeVeiculoRepository


@pytest.mark.unit
async def test_cadastrar_veiculo_persiste_e_retorna_disponivel() -> None:
    """Cadastra um veiculo valido, que nasce DISPONIVEL e e persistido."""
    # Arrange
    repositorio = FakeVeiculoRepository()
    caso = CadastrarVeiculo(repositorio)
    comando = CadastrarVeiculoCommand(
        marca="Honda",
        modelo="Civic",
        ano=2022,
        cor="Preto",
        preco=Decimal("120000.00"),
    )

    # Act
    dto = await caso.executar(comando)

    # Assert
    assert dto.status is StatusVeiculo.DISPONIVEL
    assert dto.marca == "Honda"
    assert len(repositorio.adicionados) == 1


@pytest.mark.unit
async def test_cadastrar_veiculo_preco_invalido_nao_persiste() -> None:
    """Preco nao positivo levanta ValidationError antes de qualquer persistencia."""
    # Arrange
    repositorio = FakeVeiculoRepository()
    caso = CadastrarVeiculo(repositorio)
    comando = CadastrarVeiculoCommand(
        marca="Honda",
        modelo="Civic",
        ano=2022,
        cor="Preto",
        preco=Decimal("0"),
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        await caso.executar(comando)
    assert repositorio.adicionados == []


@pytest.mark.unit
async def test_cadastrar_veiculo_ano_invalido_nao_persiste() -> None:
    """Ano implausivel levanta ValidationError e nada e persistido."""
    # Arrange
    repositorio = FakeVeiculoRepository()
    caso = CadastrarVeiculo(repositorio)
    comando = CadastrarVeiculoCommand(
        marca="Honda",
        modelo="Civic",
        ano=1800,
        cor="Preto",
        preco=Decimal("120000.00"),
    )

    # Act / Assert
    with pytest.raises(ValidationError):
        await caso.executar(comando)
    assert repositorio.adicionados == []
