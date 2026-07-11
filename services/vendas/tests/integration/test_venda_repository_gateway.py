"""Testes de integracao do VendaRepositoryGateway contra Postgres real."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Veiculo, Venda
from src.domain.exceptions import VeiculoIndisponivelError
from src.domain.value_objects import Ano, Preco, StatusVeiculo, StatusVenda
from src.interface.gateways.veiculo_repository_gateway import VeiculoRepositoryGateway
from src.interface.gateways.venda_repository_gateway import VendaRepositoryGateway


def construir_veiculo() -> Veiculo:
    """Constroi uma entidade Veiculo valida."""
    agora = datetime.now(UTC)
    return Veiculo(
        id=uuid4(),
        marca="Toyota",
        modelo="Corolla",
        ano=Ano(valor=2020),
        cor="Prata",
        preco=Preco(valor=Decimal("50000.00")),
        status=StatusVeiculo.DISPONIVEL,
        created_at=agora,
        updated_at=agora,
    )


def construir_venda(veiculo_id, cliente_id="cliente-1") -> Venda:
    """Constroi uma entidade Venda efetivada (PAGA) valida."""
    agora = datetime.now(UTC)
    return Venda(
        id=uuid4(),
        veiculo_id=veiculo_id,
        cliente_id=cliente_id,
        preco_venda=Preco(valor=Decimal("50000.00")),
        status=StatusVenda.PAGA,
        data_venda=agora,
        created_at=agora,
        updated_at=agora,
    )


@pytest.mark.integration
async def test_adicionar_e_obter_por_veiculo(db_session: AsyncSession) -> None:
    """Testa round-trip adicionar + obter_por_veiculo (VOs reconstruidos)."""
    veiculo_repo = VeiculoRepositoryGateway(db_session)
    venda_repo = VendaRepositoryGateway(db_session)

    # Arrange: insere veiculo (FK)
    veiculo = construir_veiculo()
    await veiculo_repo.adicionar(veiculo)
    await db_session.commit()

    venda = construir_venda(veiculo.id)

    # Act
    await venda_repo.adicionar(venda)
    await db_session.commit()
    recuperada = await venda_repo.obter_por_veiculo(veiculo.id)

    # Assert
    assert recuperada is not None
    assert recuperada.id == venda.id
    assert recuperada.veiculo_id == veiculo.id
    assert recuperada.cliente_id == "cliente-1"
    assert recuperada.preco_venda.valor == Decimal("50000.00")


@pytest.mark.integration
async def test_adicionar_venda_duplicada_levanta_erro(db_session: AsyncSession) -> None:
    """Testa que 2a venda do mesmo veiculo levanta VeiculoIndisponivelError."""
    veiculo_repo = VeiculoRepositoryGateway(db_session)
    venda_repo = VendaRepositoryGateway(db_session)

    # Arrange: insere veiculo
    veiculo = construir_veiculo()
    await veiculo_repo.adicionar(veiculo)
    await db_session.commit()

    venda1 = construir_venda(veiculo.id, "cliente-1")
    venda2 = construir_venda(veiculo.id, "cliente-2")

    # Act & Assert
    await venda_repo.adicionar(venda1)
    await db_session.commit()

    # A segunda venda deve falhar
    with pytest.raises(VeiculoIndisponivelError):
        await venda_repo.adicionar(venda2)


@pytest.mark.integration
async def test_obter_por_veiculo_inexistente(db_session: AsyncSession) -> None:
    """Testa que obter_por_veiculo retorna None para veiculo sem venda."""
    venda_repo = VendaRepositoryGateway(db_session)

    # Act
    resultado = await venda_repo.obter_por_veiculo(uuid4())

    # Assert
    assert resultado is None
