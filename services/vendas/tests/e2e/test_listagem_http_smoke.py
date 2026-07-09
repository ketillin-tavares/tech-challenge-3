"""Testes E2E de smoke HTTP: listagem publica de veiculos via FastAPI."""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.dtos import CadastrarVeiculoCommand
from src.application.use_cases.cadastrar_veiculo import CadastrarVeiculo
from src.domain.value_objects import StatusVeiculo
from src.interface.gateways.veiculo_repository_gateway import VeiculoRepositoryGateway


@pytest.mark.integration
@pytest.mark.e2e
async def test_listagem_http_veiculos_disponiveis_publico(
    session_factory: async_sessionmaker[AsyncSession],
    client_with_container: TestClient,
) -> None:
    """Testa GET /v1/veiculos?status=DISPONIVEL (listagem publica)."""
    # Setup: semeie 2 veiculos disponiveis
    async with session_factory() as session:
        veiculo_repo = VeiculoRepositoryGateway(session)
        cadastro_uc = CadastrarVeiculo(veiculo_repo)

        v1_cmd = CadastrarVeiculoCommand(
            marca="Toyota",
            modelo="Corolla",
            ano=2020,
            cor="Prata",
            preco=Decimal("50000.00"),
        )
        v1 = await cadastro_uc.executar(v1_cmd)

        v2_cmd = CadastrarVeiculoCommand(
            marca="Honda",
            modelo="Civic",
            ano=2021,
            cor="Preto",
            preco=Decimal("60000.00"),
        )
        v2 = await cadastro_uc.executar(v2_cmd)
        await session.commit()

        # Act: faz requisicao GET sem autenticacao
        response = client_with_container.get("/v1/veiculos?status=DISPONIVEL")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2

        # Verifica estrutura e ordenacao por preco
        assert data[0]["id"] == str(v1.id)
        assert data[0]["marca"] == "Toyota"
        assert data[0]["preco"] == "50000.00"
        assert data[0]["status"] == StatusVeiculo.DISPONIVEL.value

        assert data[1]["id"] == str(v2.id)
        assert data[1]["preco"] == "60000.00"
