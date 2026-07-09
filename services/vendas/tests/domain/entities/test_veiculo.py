"""Testes da entidade Veiculo (transicoes de estado)."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities import Veiculo
from src.domain.exceptions import VeiculoIndisponivelError, VeiculoVendidoNaoEditavelError
from src.domain.value_objects import Ano, Preco, StatusVeiculo


def _novo_veiculo(status: StatusVeiculo = StatusVeiculo.DISPONIVEL) -> Veiculo:
    """Cria um veiculo valido para os testes."""
    agora = datetime.now(UTC)
    return Veiculo(
        id=uuid4(),
        marca="Toyota",
        modelo="Corolla",
        ano=Ano(valor=2020),
        cor="Prata",
        preco=Preco(valor=Decimal("85000.00")),
        status=status,
        created_at=agora,
        updated_at=agora,
    )


@pytest.mark.unit
def test_veiculo_nasce_disponivel_por_padrao() -> None:
    """Sem status explicito, o veiculo nasce DISPONIVEL."""
    agora = datetime.now(UTC)
    veiculo = Veiculo(
        id=uuid4(),
        marca="Honda",
        modelo="Civic",
        ano=Ano(valor=2022),
        cor="Preto",
        preco=Preco(valor=Decimal("120000.00")),
        created_at=agora,
        updated_at=agora,
    )
    assert veiculo.status is StatusVeiculo.DISPONIVEL


@pytest.mark.unit
def test_marcar_como_vendido_transita_de_disponivel() -> None:
    """marcar_como_vendido muda DISPONIVEL -> VENDIDO."""
    # Arrange
    veiculo = _novo_veiculo()

    # Act
    veiculo.marcar_como_vendido()

    # Assert
    assert veiculo.status is StatusVeiculo.VENDIDO


@pytest.mark.unit
def test_marcar_como_vendido_em_vendido_levanta_erro() -> None:
    """Vender um veiculo ja VENDIDO viola a transicao unica."""
    # Arrange
    veiculo = _novo_veiculo(status=StatusVeiculo.VENDIDO)

    # Act / Assert
    with pytest.raises(VeiculoIndisponivelError):
        veiculo.marcar_como_vendido()


@pytest.mark.unit
def test_atualizar_dados_em_disponivel_substitui_campos() -> None:
    """Edicao e permitida enquanto DISPONIVEL."""
    # Arrange
    veiculo = _novo_veiculo()

    # Act
    veiculo.atualizar_dados(
        marca="Fiat",
        modelo="Pulse",
        ano=Ano(valor=2024),
        cor="Vermelho",
        preco=Preco(valor=Decimal("110000.00")),
    )

    # Assert
    assert veiculo.marca == "Fiat"
    assert veiculo.preco == Preco(valor=Decimal("110000.00"))


@pytest.mark.unit
def test_atualizar_dados_em_vendido_levanta_erro() -> None:
    """Editar um veiculo VENDIDO e proibido."""
    # Arrange
    veiculo = _novo_veiculo(status=StatusVeiculo.VENDIDO)

    # Act / Assert
    with pytest.raises(VeiculoVendidoNaoEditavelError):
        veiculo.atualizar_dados(
            marca="Fiat",
            modelo="Pulse",
            ano=Ano(valor=2024),
            cor="Vermelho",
            preco=Preco(valor=Decimal("110000.00")),
        )
