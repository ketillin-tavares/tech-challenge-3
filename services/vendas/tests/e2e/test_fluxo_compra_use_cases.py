"""Testes E2E do fluxo de compra orquestrando use cases contra container Postgres."""

from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.dtos import CadastrarVeiculoCommand, ComprarVeiculoCommand, PaginacaoQuery
from src.application.use_cases.cadastrar_veiculo import CadastrarVeiculo
from src.application.use_cases.comprar_veiculo import ComprarVeiculo
from src.application.use_cases.listar_disponiveis import ListarDisponiveis
from src.application.use_cases.listar_vendidos import ListarVendidos
from src.domain.exceptions import VeiculoIndisponivelError, VeiculoNaoEncontradoError
from src.domain.value_objects import StatusVeiculo
from src.interface.gateways.unit_of_work_gateway import UnitOfWorkGateway
from src.interface.gateways.veiculo_query_service_gateway import VeiculoQueryServiceGateway
from src.interface.gateways.veiculo_repository_gateway import VeiculoRepositoryGateway


@pytest.mark.integration
@pytest.mark.e2e
async def test_fluxo_cadastro_listagem_compra(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Testa fluxo: cadastra -> aparece disponiveis -> compra -> vendidos."""
    # Setup com sessao dedicada para os gateways
    async with session_factory() as session:
        veiculo_repo = VeiculoRepositoryGateway(session)
        query_service = VeiculoQueryServiceGateway(session)
        uow = UnitOfWorkGateway(session_factory)

        cadastro_uc = CadastrarVeiculo(veiculo_repo)
        listagem_uc = ListarDisponiveis(query_service)
        compra_uc = ComprarVeiculo(uow)
        vendidos_uc = ListarVendidos(query_service)

        # Act 1: Cadastra veiculo
        cmd_cadastro = CadastrarVeiculoCommand(
            marca="Toyota",
            modelo="Corolla",
            ano=2020,
            cor="Prata",
            preco=Decimal("50000.00"),
        )
        veiculo_dto = await cadastro_uc.executar(cmd_cadastro)
        await session.commit()

        # Assert 1: Veiculo aparece em disponiveis
        paginacao = PaginacaoQuery(limit=50, offset=0)
        disponiveis = await listagem_uc.executar(paginacao)
        assert len(disponiveis) == 1
        assert disponiveis[0].id == veiculo_dto.id
        assert disponiveis[0].status == StatusVeiculo.DISPONIVEL

        # Act 2: Compra o veiculo
        cmd_compra = ComprarVeiculoCommand(
            veiculo_id=veiculo_dto.id,
            cliente_id="cliente-teste",
        )
        recibo = await compra_uc.executar(cmd_compra)

        # Assert 2: Veiculo saiu de disponiveis
        disponiveis_after = await listagem_uc.executar(paginacao)
        assert len(disponiveis_after) == 0

        # Assert 3: Veiculo aparece em vendidos com dados corretos
        vendidos = await vendidos_uc.executar(paginacao)
        assert len(vendidos) == 1
        dto_vendido = vendidos[0]
        assert dto_vendido.id == veiculo_dto.id
        assert dto_vendido.status == StatusVeiculo.VENDIDO
        assert dto_vendido.preco_venda == Decimal("50000.00")
        assert dto_vendido.data_venda == recibo.data_venda


@pytest.mark.integration
@pytest.mark.e2e
async def test_recompra_mesmo_veiculo_levanta_erro(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Testa que tentar comprar o mesmo veiculo 2x levanta VeiculoIndisponivelError."""
    # Setup
    async with session_factory() as session:
        veiculo_repo = VeiculoRepositoryGateway(session)
        uow = UnitOfWorkGateway(session_factory)

        cadastro_uc = CadastrarVeiculo(veiculo_repo)
        compra_uc = ComprarVeiculo(uow)

        # Cadastra veiculo
        cmd_cadastro = CadastrarVeiculoCommand(
            marca="Honda",
            modelo="Civic",
            ano=2021,
            cor="Preto",
            preco=Decimal("80000.00"),
        )
        veiculo_dto = await cadastro_uc.executar(cmd_cadastro)
        await session.commit()

        # Compra a primeira vez
        cmd_compra1 = ComprarVeiculoCommand(
            veiculo_id=veiculo_dto.id,
            cliente_id="cliente-1",
        )
        await compra_uc.executar(cmd_compra1)

        # Tenta comprar novamente
        cmd_compra2 = ComprarVeiculoCommand(
            veiculo_id=veiculo_dto.id,
            cliente_id="cliente-2",
        )

        with pytest.raises(VeiculoIndisponivelError):
            await compra_uc.executar(cmd_compra2)


@pytest.mark.integration
@pytest.mark.e2e
async def test_compra_veiculo_inexistente_levanta_erro(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Testa que comprar veiculo inexistente levanta VeiculoNaoEncontradoError."""
    # Setup
    uow = UnitOfWorkGateway(session_factory)
    compra_uc = ComprarVeiculo(uow)

    # Tenta comprar veiculo inexistente
    cmd_compra = ComprarVeiculoCommand(
        veiculo_id=uuid4(),
        cliente_id="cliente-1",
    )

    with pytest.raises(VeiculoNaoEncontradoError):
        await compra_uc.executar(cmd_compra)


@pytest.mark.integration
@pytest.mark.e2e
async def test_multiplos_veiculos_listagem_correta(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Testa que multiplos veiculos sao listados e vendidos corretamente."""
    # Setup
    async with session_factory() as session:
        veiculo_repo = VeiculoRepositoryGateway(session)
        query_service = VeiculoQueryServiceGateway(session)
        uow = UnitOfWorkGateway(session_factory)

        cadastro_uc = CadastrarVeiculo(veiculo_repo)
        listagem_uc = ListarDisponiveis(query_service)
        compra_uc = ComprarVeiculo(uow)
        vendidos_uc = ListarVendidos(query_service)

        # Cadastra 3 veiculos
        veiculos_ids = []
        for i in range(3):
            cmd = CadastrarVeiculoCommand(
                marca=f"Marca{i}",
                modelo=f"Modelo{i}",
                ano=2020 + i,
                cor=f"Cor{i}",
                preco=Decimal(str(30000 + i * 10000)),
            )
            dto = await cadastro_uc.executar(cmd)
            veiculos_ids.append(dto.id)

        await session.commit()

        # Verifica 3 disponiveis
        paginacao = PaginacaoQuery(limit=50, offset=0)
        disponiveis = await listagem_uc.executar(paginacao)
        assert len(disponiveis) == 3
        # Ordenacao por preco
        assert disponiveis[0].preco == Decimal("30000.00")
        assert disponiveis[1].preco == Decimal("40000.00")
        assert disponiveis[2].preco == Decimal("50000.00")

        # Compra 2
        await compra_uc.executar(
            ComprarVeiculoCommand(veiculo_id=veiculos_ids[0], cliente_id="cli1")
        )
        await compra_uc.executar(
            ComprarVeiculoCommand(veiculo_id=veiculos_ids[1], cliente_id="cli2")
        )

        # Verifica 1 disponivel, 2 vendidos
        disponiveis_after = await listagem_uc.executar(paginacao)
        vendidos = await vendidos_uc.executar(paginacao)
        assert len(disponiveis_after) == 1
        assert len(vendidos) == 2
