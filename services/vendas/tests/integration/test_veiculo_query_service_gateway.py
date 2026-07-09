"""Testes de integracao do VeiculoQueryServiceGateway contra Postgres real."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Veiculo, Venda
from src.domain.value_objects import Ano, Preco, StatusVeiculo
from src.interface.gateways.veiculo_query_service_gateway import VeiculoQueryServiceGateway
from src.interface.gateways.veiculo_repository_gateway import VeiculoRepositoryGateway
from src.interface.gateways.venda_repository_gateway import VendaRepositoryGateway


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


def construir_venda(veiculo_id) -> Venda:
    """Constroi uma entidade Venda valida."""
    agora = datetime.now(UTC)
    return Venda(
        id=uuid4(),
        veiculo_id=veiculo_id,
        cliente_id="cliente-1",
        preco_venda=Preco(valor=Decimal("60000.00")),
        data_venda=agora,
        created_at=agora,
    )


@pytest.mark.integration
async def test_listar_disponiveis_filtra_e_ordena(db_session: AsyncSession) -> None:
    """Testa que listar_disponiveis filtra DISPONIVEL e ordena por preco."""
    veiculo_repo = VeiculoRepositoryGateway(db_session)
    query_service = VeiculoQueryServiceGateway(db_session)

    # Arrange: insere veiculos disponiveis e vendidos
    v1 = construir_veiculo(status=StatusVeiculo.DISPONIVEL, preco="30000.00")
    v2 = construir_veiculo(status=StatusVeiculo.DISPONIVEL, preco="50000.00")
    v3 = construir_veiculo(status=StatusVeiculo.VENDIDO, preco="40000.00")

    await veiculo_repo.adicionar(v1)
    await veiculo_repo.adicionar(v2)
    await veiculo_repo.adicionar(v3)
    await db_session.commit()

    # Act
    resultado = await query_service.listar_disponiveis()

    # Assert
    assert len(resultado) == 2
    assert resultado[0].preco == Decimal("30000.00")
    assert resultado[1].preco == Decimal("50000.00")
    assert all(r.status == StatusVeiculo.DISPONIVEL for r in resultado)


@pytest.mark.integration
async def test_listar_disponiveis_paginacao(db_session: AsyncSession) -> None:
    """Testa que paginacao funciona em listar_disponiveis."""
    veiculo_repo = VeiculoRepositoryGateway(db_session)
    query_service = VeiculoQueryServiceGateway(db_session)

    # Arrange: insere 5 disponiveis
    for i in range(5):
        v = construir_veiculo(preco=str(10000 + i * 10000))
        await veiculo_repo.adicionar(v)
    await db_session.commit()

    # Act
    page1 = await query_service.listar_disponiveis(limit=2, offset=0)
    page2 = await query_service.listar_disponiveis(limit=2, offset=2)

    # Assert
    assert len(page1) == 2
    assert len(page2) == 2
    assert page1[0].preco == Decimal("10000.00")
    assert page2[0].preco == Decimal("30000.00")


@pytest.mark.integration
async def test_listar_vendidos_join_correto(db_session: AsyncSession) -> None:
    """Testa que listar_vendidos faz JOIN correto e retorna preco_venda/data_venda."""
    veiculo_repo = VeiculoRepositoryGateway(db_session)
    venda_repo = VendaRepositoryGateway(db_session)
    query_service = VeiculoQueryServiceGateway(db_session)

    # Arrange: insere veiculo, marca como vendido, insere venda
    veiculo = construir_veiculo(status=StatusVeiculo.DISPONIVEL, preco="50000.00")
    await veiculo_repo.adicionar(veiculo)
    await db_session.commit()

    veiculo_vendido = construir_veiculo(
        status=StatusVeiculo.VENDIDO,
        preco="50000.00",
    )
    veiculo_vendido.id = veiculo.id
    await veiculo_repo.atualizar(veiculo_vendido)

    venda = construir_venda(veiculo.id)
    await venda_repo.adicionar(venda)
    await db_session.commit()

    # Act
    resultado = await query_service.listar_vendidos()

    # Assert
    assert len(resultado) == 1
    dto = resultado[0]
    assert dto.id == veiculo.id
    assert dto.status == StatusVeiculo.VENDIDO
    assert dto.preco == Decimal("50000.00")
    assert dto.preco_venda == Decimal("60000.00")
    assert dto.data_venda == venda.data_venda


@pytest.mark.integration
async def test_listar_vendidos_paginacao(db_session: AsyncSession) -> None:
    """Testa que paginacao funciona em listar_vendidos."""
    veiculo_repo = VeiculoRepositoryGateway(db_session)
    venda_repo = VendaRepositoryGateway(db_session)
    query_service = VeiculoQueryServiceGateway(db_session)

    # Arrange: insere 3 vendas
    for i in range(3):
        v = construir_veiculo(status=StatusVeiculo.VENDIDO, preco=str(10000 + i * 10000))
        await veiculo_repo.adicionar(v)

        venda = construir_venda(v.id)
        await venda_repo.adicionar(venda)

    await db_session.commit()

    # Act
    page1 = await query_service.listar_vendidos(limit=2, offset=0)
    page2 = await query_service.listar_vendidos(limit=2, offset=2)

    # Assert
    assert len(page1) == 2
    assert len(page2) == 1
