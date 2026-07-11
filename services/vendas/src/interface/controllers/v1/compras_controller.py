"""Controller do contexto de Compras (/v1/compras).

Exige cliente autenticado; o `cliente_id` vem do `sub` do JWT, nunca do body.
Compra e efetivacao sao etapas distintas: POST /v1/compras reserva o veiculo
(venda PENDENTE) e as transicoes (efetivacao/cancelamento) sao endpoints
proprios, acessiveis ao dono da venda ou a um admin. O wiring dos casos de
uso acontece aqui, na borda.
"""

from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter

from src.application.dtos.venda import (
    IniciarCompraCommand,
    IniciarCompraRequest,
    ReciboVendaDTO,
    TransicaoCompraCommand,
)
from src.application.use_cases.cancelar_compra import CancelarCompra
from src.application.use_cases.efetivar_compra import EfetivarCompra
from src.application.use_cases.iniciar_compra import IniciarCompra
from src.application.use_cases.obter_compra import ObterCompra
from src.domain.value_objects import ClienteAutenticado
from src.environment import get_settings
from src.infrastructure.database import async_session_factory
from src.interface.controllers.dependencies import GRUPO_ADMIN, ClienteDep
from src.interface.gateways.unit_of_work_gateway import UnitOfWorkGateway

router = APIRouter(prefix="/v1/compras", tags=["compras"])


def _comando_transicao(venda_id: UUID, cliente: ClienteAutenticado) -> TransicaoCompraCommand:
    """Monta o comando de transicao/consulta a partir da identidade do JWT.

    Args:
        venda_id: Identificador da venda alvo (path).
        cliente: Identidade autenticada (sub e grupos).

    Returns:
        Comando com o par cliente/admin usado na autorizacao dono-ou-admin.
    """
    return TransicaoCompraCommand(
        venda_id=venda_id,
        cliente_id=cliente.sub,
        eh_admin=cliente.tem_grupo(GRUPO_ADMIN),
    )


@router.post("", status_code=201, response_model=ReciboVendaDTO)
async def iniciar_compra(dados: IniciarCompraRequest, cliente: ClienteDep) -> ReciboVendaDTO:
    """Inicia a compra de um veiculo (reserva com prazo) pelo cliente autenticado.

    Args:
        dados: Corpo da requisicao com o id do veiculo.
        cliente: Identidade autenticada (origem do `cliente_id`).

    Returns:
        Recibo da venda PENDENTE criada (com `expira_em`).
    """
    settings = get_settings()
    caso = IniciarCompra(
        UnitOfWorkGateway(async_session_factory),
        reserva_ttl=timedelta(minutes=settings.compra.reserva_ttl_minutos),
    )
    comando = IniciarCompraCommand(veiculo_id=dados.veiculo_id, cliente_id=cliente.sub)
    return await caso.executar(comando)


@router.post("/{venda_id}/efetivacao", response_model=ReciboVendaDTO)
async def efetivar_compra(venda_id: UUID, cliente: ClienteDep) -> ReciboVendaDTO:
    """Efetiva a compra (confirmacao do pagamento) da venda PENDENTE.

    Idempotente para vendas ja PAGAS. Acessivel ao dono da venda ou a admins.

    Args:
        venda_id: Identificador da venda a efetivar.
        cliente: Identidade autenticada.

    Returns:
        Recibo da venda efetivada (status PAGA).
    """
    caso = EfetivarCompra(UnitOfWorkGateway(async_session_factory))
    return await caso.executar(_comando_transicao(venda_id, cliente))


@router.post("/{venda_id}/cancelamento", response_model=ReciboVendaDTO)
async def cancelar_compra(venda_id: UUID, cliente: ClienteDep) -> ReciboVendaDTO:
    """Cancela a compra PENDENTE, devolvendo o veiculo a DISPONIVEL.

    Idempotente para vendas ja CANCELADAS. Acessivel ao dono ou a admins.

    Args:
        venda_id: Identificador da venda a cancelar.
        cliente: Identidade autenticada.

    Returns:
        Recibo da venda cancelada (status CANCELADA).
    """
    caso = CancelarCompra(UnitOfWorkGateway(async_session_factory))
    return await caso.executar(_comando_transicao(venda_id, cliente))


@router.get("/{venda_id}", response_model=ReciboVendaDTO)
async def obter_compra(venda_id: UUID, cliente: ClienteDep) -> ReciboVendaDTO:
    """Consulta o estado atual da compra (dono da venda ou admin).

    Args:
        venda_id: Identificador da venda.
        cliente: Identidade autenticada.

    Returns:
        Recibo com o estado atual da venda.
    """
    caso = ObterCompra(UnitOfWorkGateway(async_session_factory))
    return await caso.executar(_comando_transicao(venda_id, cliente))
