"""Caso de uso: cancelar a compra de um veiculo (desistencia)."""

from datetime import UTC, datetime

from src.application.dtos import ReciboVendaDTO, TransicaoCompraCommand
from src.application.use_cases.acesso_venda import verificar_acesso_venda
from src.domain.exceptions import TransicaoVendaInvalidaError, VeiculoNaoEncontradoError
from src.domain.repositories import UnitOfWork
from src.domain.value_objects import StatusVenda


class CancelarCompra:
    """Cancela uma venda PENDENTE de forma atomica.

    Transita a venda para CANCELADA e devolve o veiculo a DISPONIVEL na mesma
    transacao, liberando-o para nova compra (inclusive do mesmo cliente).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        """Recebe a unidade de trabalho por injecao.

        Args:
            uow: Unidade de trabalho que coordena a transacao atomica.
        """
        self._uow = uow

    async def executar(self, comando: TransicaoCompraCommand) -> ReciboVendaDTO:
        """Cancela a venda do cliente autenticado (ou de qualquer um, se admin).

        Idempotente: cancelar uma venda ja CANCELADA retorna o recibo sem
        alterar nada. Cancelar uma venda PAGA e uma transicao invalida.

        Args:
            comando: Venda alvo e identidade do solicitante (sub/admin).

        Returns:
            Recibo da venda cancelada (status CANCELADA).

        Raises:
            VendaNaoEncontradaError: Se a venda nao existe ou e de outro cliente.
            TransicaoVendaInvalidaError: Se a venda ja foi PAGA.
            VeiculoNaoEncontradoError: Se o veiculo da venda nao existir.
        """
        async with self._uow as uow:
            venda = verificar_acesso_venda(await uow.vendas.obter_por_id(comando.venda_id), comando)
            if venda.status is StatusVenda.CANCELADA:
                return ReciboVendaDTO.de_venda(venda)
            if venda.status is StatusVenda.PAGA:
                raise TransicaoVendaInvalidaError(venda.id)

            agora = datetime.now(UTC)
            venda.cancelar(agora)
            veiculo = await uow.veiculos.obter_por_id(venda.veiculo_id)
            if veiculo is None:
                raise VeiculoNaoEncontradoError(venda.veiculo_id)
            veiculo.liberar_reserva()

            await uow.vendas.atualizar(venda)
            await uow.veiculos.atualizar(veiculo)
            await uow.commit()
            return ReciboVendaDTO.de_venda(venda)
