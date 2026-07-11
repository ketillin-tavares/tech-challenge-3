"""Controller do contexto de Veiculos (/v1/veiculos).

Listagens publicas; cadastro e edicao exigem o grupo `admin`. O wiring dos
casos de uso (instanciacao do gateway concreto + injecao) acontece aqui, na
borda; os casos de uso recebem apenas Ports.
"""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.paginacao import PaginacaoQuery
from src.application.dtos.veiculo import (
    CadastrarVeiculoCommand,
    EditarVeiculoCommand,
    EditarVeiculoRequest,
    VeiculoDTO,
    VeiculoVendidoDTO,
)
from src.application.use_cases.cadastrar_veiculo import CadastrarVeiculo
from src.application.use_cases.editar_veiculo import EditarVeiculo
from src.application.use_cases.listar_disponiveis import ListarDisponiveis
from src.application.use_cases.listar_vendidos import ListarVendidos
from src.domain.value_objects import StatusVeiculo
from src.infrastructure.database import get_session
from src.interface.controllers.dependencies import requer_admin
from src.interface.gateways.veiculo_query_service_gateway import VeiculoQueryServiceGateway
from src.interface.gateways.veiculo_repository_gateway import VeiculoRepositoryGateway

router = APIRouter(prefix="/v1/veiculos", tags=["veiculos"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]


@router.post(
    "",
    status_code=201,
    response_model=VeiculoDTO,
    dependencies=[Depends(requer_admin)],
)
async def cadastrar_veiculo(comando: CadastrarVeiculoCommand, session: SessionDep) -> VeiculoDTO:
    """Cadastra um novo veiculo (somente admin).

    Args:
        comando: Dados do veiculo a cadastrar.
        session: Sessao de banco injetada.

    Returns:
        O veiculo cadastrado.
    """
    caso = CadastrarVeiculo(VeiculoRepositoryGateway(session))
    return await caso.executar(comando)


@router.put(
    "/{veiculo_id}",
    response_model=VeiculoDTO,
    dependencies=[Depends(requer_admin)],
)
async def editar_veiculo(
    veiculo_id: UUID,
    dados: EditarVeiculoRequest,
    session: SessionDep,
) -> VeiculoDTO:
    """Edita um veiculo existente (somente admin).

    Args:
        veiculo_id: Identificador do veiculo (vem do path).
        dados: Novos dados do veiculo.
        session: Sessao de banco injetada.

    Returns:
        O veiculo atualizado.
    """
    caso = EditarVeiculo(VeiculoRepositoryGateway(session))
    comando = EditarVeiculoCommand(veiculo_id=veiculo_id, **dados.model_dump())
    return await caso.executar(comando)


@router.get("", response_model=list[VeiculoDTO] | list[VeiculoVendidoDTO])
async def listar_veiculos(
    status: Annotated[Literal[StatusVeiculo.DISPONIVEL, StatusVeiculo.VENDIDO], Query()],
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[VeiculoDTO] | list[VeiculoVendidoDTO]:
    """Lista veiculos por status (publico), ordenados por preco ascendente.

    Somente as vitrines publicas existem como listagem: DISPONIVEL e VENDIDO.
    RESERVADO nao e listavel (o veiculo apenas sai da vitrine de disponiveis
    enquanto a compra esta pendente) -> 422.

    Args:
        status: Status dos veiculos a listar (DISPONIVEL ou VENDIDO).
        session: Sessao de banco injetada.
        limit: Quantidade maxima de itens por pagina.
        offset: Deslocamento de paginacao.

    Returns:
        Lista de veiculos disponiveis ou vendidos, conforme o status.
    """
    paginacao = PaginacaoQuery(limit=limit, offset=offset)
    if status is StatusVeiculo.DISPONIVEL:
        caso_disponiveis = ListarDisponiveis(VeiculoQueryServiceGateway(session))
        return await caso_disponiveis.executar(paginacao)
    caso_vendidos = ListarVendidos(VeiculoQueryServiceGateway(session))
    return await caso_vendidos.executar(paginacao)
