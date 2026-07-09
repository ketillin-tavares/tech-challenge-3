"""Testes de integracao do VeiculoRepositoryGateway contra Postgres real."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Veiculo
from src.domain.value_objects import Ano, Preco, StatusVeiculo
from src.interface.gateways.veiculo_repository_gateway import VeiculoRepositoryGateway


def construir_veiculo(
    *,
    status: StatusVeiculo = StatusVeiculo.DISPONIVEL,
    preco: str = "50000.00",
) -> Veiculo:
    """Constroi uma entidade Veiculo valida."""
    agora = datetime.now(UTC)
    return Veiculo(
        id=uuid4(),
        marca="Toyota",
        modelo="Corolla",
        ano=Ano(valor=2020),
        cor="Prata",
        preco=Preco(valor=Decimal(preco)),
        status=status,
        created_at=agora,
        updated_at=agora,
    )


@pytest.mark.integration
async def test_adicionar_e_obter_por_id(db_session: AsyncSession) -> None:
    """Testa round-trip adicionar + obter (VOs reconstruidos corretamente)."""
    repo = VeiculoRepositoryGateway(db_session)

    # Arrange
    veiculo = construir_veiculo(preco="85000.00")

    # Act
    await repo.adicionar(veiculo)
    await db_session.commit()
    recuperado = await repo.obter_por_id(veiculo.id)

    # Assert
    assert recuperado is not None
    assert recuperado.id == veiculo.id
    assert recuperado.marca == "Toyota"
    assert recuperado.modelo == "Corolla"
    assert recuperado.ano.valor == 2020
    assert recuperado.cor == "Prata"
    assert recuperado.preco.valor == Decimal("85000.00")
    assert recuperado.status == StatusVeiculo.DISPONIVEL


@pytest.mark.integration
async def test_obter_por_id_inexistente(db_session: AsyncSession) -> None:
    """Testa que obter_por_id retorna None para id inexistente."""
    repo = VeiculoRepositoryGateway(db_session)

    # Act
    resultado = await repo.obter_por_id(uuid4())

    # Assert
    assert resultado is None


@pytest.mark.integration
async def test_listar_por_status_ordena_por_preco(db_session: AsyncSession) -> None:
    """Testa que listar_por_status ordena por preco ascendente."""
    repo = VeiculoRepositoryGateway(db_session)

    # Arrange: insere 3 veiculos em ordem aleatoria de preco
    v1 = construir_veiculo(preco="30000.00")
    v2 = construir_veiculo(preco="50000.00")
    v3 = construir_veiculo(preco="40000.00")

    await repo.adicionar(v1)
    await repo.adicionar(v2)
    await repo.adicionar(v3)
    await db_session.commit()

    # Act
    lista = await repo.listar_por_status(StatusVeiculo.DISPONIVEL)

    # Assert
    assert len(lista) == 3
    assert lista[0].preco.valor == Decimal("30000.00")
    assert lista[1].preco.valor == Decimal("40000.00")
    assert lista[2].preco.valor == Decimal("50000.00")


@pytest.mark.integration
async def test_listar_por_status_paginacao(db_session: AsyncSession) -> None:
    """Testa que limit/offset funcionam."""
    repo = VeiculoRepositoryGateway(db_session)

    # Arrange: insere 5 veiculos
    for i in range(5):
        v = construir_veiculo(preco=str(10000 + i * 10000))
        await repo.adicionar(v)
    await db_session.commit()

    # Act
    page1 = await repo.listar_por_status(StatusVeiculo.DISPONIVEL, limit=2, offset=0)
    page2 = await repo.listar_por_status(StatusVeiculo.DISPONIVEL, limit=2, offset=2)
    page3 = await repo.listar_por_status(StatusVeiculo.DISPONIVEL, limit=2, offset=4)

    # Assert
    assert len(page1) == 2
    assert len(page2) == 2
    assert len(page3) == 1
    assert page1[0].preco.valor == Decimal("10000.00")
    assert page2[0].preco.valor == Decimal("30000.00")
    assert page3[0].preco.valor == Decimal("50000.00")


@pytest.mark.integration
async def test_listar_por_status_filtra_por_status(db_session: AsyncSession) -> None:
    """Testa que listar_por_status filtra corretamente pelo status."""
    repo = VeiculoRepositoryGateway(db_session)

    # Arrange
    v_disp = construir_veiculo(status=StatusVeiculo.DISPONIVEL)
    v_vend = construir_veiculo(status=StatusVeiculo.VENDIDO)

    await repo.adicionar(v_disp)
    await repo.adicionar(v_vend)
    await db_session.commit()

    # Act
    disponiveis = await repo.listar_por_status(StatusVeiculo.DISPONIVEL)
    vendidos = await repo.listar_por_status(StatusVeiculo.VENDIDO)

    # Assert
    assert len(disponiveis) == 1
    assert disponiveis[0].status == StatusVeiculo.DISPONIVEL
    assert len(vendidos) == 1
    assert vendidos[0].status == StatusVeiculo.VENDIDO


@pytest.mark.integration
async def test_atualizar_veiculo(db_session: AsyncSession) -> None:
    """Testa que atualizar modifica corretamente um veiculo."""
    repo = VeiculoRepositoryGateway(db_session)

    # Arrange
    veiculo = construir_veiculo()
    await repo.adicionar(veiculo)
    await db_session.commit()

    # Modifica em memoria
    veiculo.marca = "Honda"
    veiculo.preco = Preco(valor=Decimal("95000.00"))
    veiculo.status = StatusVeiculo.VENDIDO

    # Act
    await repo.atualizar(veiculo)
    await db_session.commit()

    # Reabra sessao para garantir leitura fresca do BD
    recuperado = await repo.obter_por_id(veiculo.id)

    # Assert
    assert recuperado is not None
    assert recuperado.marca == "Honda"
    assert recuperado.preco.valor == Decimal("95000.00")
    assert recuperado.status == StatusVeiculo.VENDIDO
