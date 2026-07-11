"""Testes de integracao do UnitOfWorkGateway contra Postgres real."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.entities import Veiculo, Venda
from src.domain.value_objects import Ano, Preco, StatusVeiculo, StatusVenda
from src.interface.gateways.unit_of_work_gateway import UnitOfWorkGateway
from src.interface.gateways.veiculo_repository_gateway import VeiculoRepositoryGateway


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


def construir_venda(veiculo_id) -> Venda:
    """Constroi uma entidade Venda efetivada (PAGA) valida."""
    agora = datetime.now(UTC)
    return Venda(
        id=uuid4(),
        veiculo_id=veiculo_id,
        cliente_id="cliente-1",
        preco_venda=Preco(valor=Decimal("50000.00")),
        status=StatusVenda.PAGA,
        data_venda=agora,
        created_at=agora,
        updated_at=agora,
    )


@pytest.mark.integration
async def test_commit_persiste_dados(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Testa que commit() persiste dados e sao visiveis em nova sessao."""
    # Arrange
    veiculo = construir_veiculo()
    uow = UnitOfWorkGateway(session_factory)

    # Act: adiciona via UoW
    async with uow as u:
        await u.veiculos.adicionar(veiculo)
        await u.commit()

    # Reabre uma sessao nova (fechada ao fim) para verificar persistencia
    async with session_factory() as verificacao:
        recuperado = await VeiculoRepositoryGateway(verificacao).obter_por_id(veiculo.id)

    # Assert
    assert recuperado is not None
    assert recuperado.id == veiculo.id


@pytest.mark.integration
async def test_rollback_em_excecao_nao_persiste(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Testa que excecao dentro do async with faz rollback (nada nao-commitado persiste)."""
    # Arrange
    veiculo = construir_veiculo()
    uow = UnitOfWorkGateway(session_factory)

    # Act & Assert: adiciona SEM commit e levanta erro -> __aexit__ faz rollback
    with pytest.raises(RuntimeError):
        async with uow as u:
            await u.veiculos.adicionar(veiculo)
            raise RuntimeError("falha simulada antes do commit")

    # Verifica que NADA foi persistido (sessao nova, fechada ao fim)
    async with session_factory() as verificacao:
        recuperado = await VeiculoRepositoryGateway(verificacao).obter_por_id(veiculo.id)

    assert recuperado is None


@pytest.mark.integration
async def test_multi_step_transacao_atomica(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Testa que multi-step (veiculo + venda) ocorre atomicamente."""
    # Arrange
    veiculo = construir_veiculo()
    veiculo.status = StatusVeiculo.DISPONIVEL

    uow = UnitOfWorkGateway(session_factory)

    # Act: executa multi-step atomico
    async with uow as u:
        await u.veiculos.adicionar(veiculo)

        # Marca como vendido
        veiculo.status = StatusVeiculo.VENDIDO
        await u.veiculos.atualizar(veiculo)

        # Insere venda
        venda = construir_venda(veiculo.id)
        await u.vendas.adicionar(venda)

        await u.commit()

    # Verifica que tudo foi persistido (sessao nova, fechada ao fim)
    async with session_factory() as verificacao:
        recuperado = await VeiculoRepositoryGateway(verificacao).obter_por_id(veiculo.id)

    assert recuperado is not None
    assert recuperado.status == StatusVeiculo.VENDIDO
