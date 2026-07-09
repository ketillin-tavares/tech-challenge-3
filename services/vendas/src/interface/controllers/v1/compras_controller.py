"""Controller do contexto de Compras (/v1/compras).

Exige cliente autenticado; o `cliente_id` vem do `sub` do JWT, nunca do body.
O wiring do caso de uso acontece aqui, na borda.
"""

from fastapi import APIRouter

from src.application.dtos.venda import (
    ComprarVeiculoCommand,
    ComprarVeiculoRequest,
    ReciboVendaDTO,
)
from src.application.use_cases.comprar_veiculo import ComprarVeiculo
from src.infrastructure.database import async_session_factory
from src.interface.controllers.dependencies import ClienteDep
from src.interface.gateways.unit_of_work_gateway import UnitOfWorkGateway

router = APIRouter(prefix="/v1/compras", tags=["compras"])


@router.post("", status_code=201, response_model=ReciboVendaDTO)
async def comprar_veiculo(dados: ComprarVeiculoRequest, cliente: ClienteDep) -> ReciboVendaDTO:
    """Efetiva a compra de um veiculo pelo cliente autenticado.

    Args:
        dados: Corpo da requisicao com o id do veiculo.
        cliente: Identidade autenticada (origem do `cliente_id`).

    Returns:
        Recibo da venda efetivada.
    """
    caso = ComprarVeiculo(UnitOfWorkGateway(async_session_factory))
    comando = ComprarVeiculoCommand(veiculo_id=dados.veiculo_id, cliente_id=cliente.sub)
    return await caso.executar(comando)
