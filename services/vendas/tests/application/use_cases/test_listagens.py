"""Testes unitarios dos casos de uso de listagem (read-model fake)."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from src.application.dtos import PaginacaoQuery, VeiculoDTO, VeiculoVendidoDTO
from src.application.use_cases.listar_disponiveis import ListarDisponiveis
from src.application.use_cases.listar_vendidos import ListarVendidos
from src.domain.entities import Venda
from src.domain.value_objects import Preco, StatusVeiculo
from tests.application.conftest import FakeVeiculoQueryService, construir_veiculo


@pytest.mark.unit
async def test_listar_disponiveis_repassa_paginacao_e_retorna_dtos() -> None:
    """ListarDisponiveis delega ao query service com a paginacao informada."""
    # Arrange
    veiculo = construir_veiculo(status=StatusVeiculo.DISPONIVEL)
    dto = VeiculoDTO.de_entidade(veiculo)
    consultas = FakeVeiculoQueryService(disponiveis=[dto])
    caso = ListarDisponiveis(consultas)

    # Act
    resultado = await caso.executar(PaginacaoQuery(limit=10, offset=5))

    # Assert
    assert resultado == [dto]
    assert consultas.chamadas_disponiveis == [(10, 5)]


@pytest.mark.unit
async def test_listar_vendidos_repassa_paginacao_e_retorna_dtos() -> None:
    """ListarVendidos delega ao query service e devolve DTOs enriquecidos."""
    # Arrange
    veiculo = construir_veiculo(status=StatusVeiculo.VENDIDO)
    agora = datetime.now(UTC)
    venda = Venda(
        id=uuid4(),
        veiculo_id=veiculo.id,
        cliente_id="sub-abc",
        preco_venda=Preco(valor=Decimal("85000.00")),
        data_venda=agora,
        created_at=agora,
    )
    dto = VeiculoVendidoDTO.de_entidades(veiculo, venda)
    consultas = FakeVeiculoQueryService(vendidos=[dto])
    caso = ListarVendidos(consultas)

    # Act
    resultado = await caso.executar(PaginacaoQuery(limit=10, offset=5))

    # Assert
    assert resultado == [dto]
    assert resultado[0].preco_venda == Decimal("85000.00")
    assert consultas.chamadas_vendidos == [(10, 5)]


@pytest.mark.unit
async def test_paginacao_rejeita_valores_invalidos() -> None:
    """Limite/offset fora do intervalo falham na validacao (borda -> 422)."""
    # Arrange / Act / Assert
    with pytest.raises(ValueError):
        PaginacaoQuery(limit=0, offset=0)
    with pytest.raises(ValueError):
        PaginacaoQuery(limit=10, offset=-1)
