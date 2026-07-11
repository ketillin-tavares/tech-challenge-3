"""Caso de uso: efetivar a compra de um veiculo (confirmacao do pagamento).

Hoje a efetivacao e acionada pelo proprio cliente (simula a confirmacao do
pagamento). Um gateway de pagamento real entraria como novo driving adapter
(ex.: webhook) chamando ESTE mesmo caso de uso, sem mudanca de contrato.
"""

from datetime import UTC, datetime

from src.application.dtos import ReciboVendaDTO, TransicaoCompraCommand
from src.application.use_cases.acesso_venda import verificar_acesso_venda
from src.domain.entities import Venda
from src.domain.exceptions import (
    ReservaExpiradaError,
    TransicaoVendaInvalidaError,
    VeiculoNaoEncontradoError,
)
from src.domain.repositories import UnitOfWork
from src.domain.value_objects import StatusVenda


class EfetivarCompra:
    """Efetiva uma venda PENDENTE de forma atomica.

    Transita a venda para PAGA e o veiculo para VENDIDO na mesma transacao.
    Reserva expirada e cancelada (venda CANCELADA + veiculo DISPONIVEL) na
    mesma chamada, antes de o erro ser propagado (expiracao lazy).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        """Recebe a unidade de trabalho por injecao.

        Args:
            uow: Unidade de trabalho que coordena a transacao atomica.
        """
        self._uow = uow

    async def executar(self, comando: TransicaoCompraCommand) -> ReciboVendaDTO:
        """Efetiva a venda do cliente autenticado (ou de qualquer um, se admin).

        Idempotente: efetivar uma venda ja PAGA retorna o recibo sem alterar
        nada. Efetivar uma venda CANCELADA e uma transicao invalida.

        Args:
            comando: Venda alvo e identidade do solicitante (sub/admin).

        Returns:
            Recibo da venda efetivada (status PAGA, `data_venda` preenchida).

        Raises:
            VendaNaoEncontradaError: Se a venda nao existe ou e de outro cliente.
            TransicaoVendaInvalidaError: Se a venda ja foi CANCELADA.
            ReservaExpiradaError: Se a reserva venceu (a venda e cancelada e o
                veiculo liberado antes de o erro ser propagado).
            VeiculoNaoEncontradoError: Se o veiculo da venda nao existir.
        """
        async with self._uow as uow:
            venda = verificar_acesso_venda(await uow.vendas.obter_por_id(comando.venda_id), comando)
            if venda.status is StatusVenda.PAGA:
                return ReciboVendaDTO.de_venda(venda)
            if venda.status is StatusVenda.CANCELADA:
                raise TransicaoVendaInvalidaError(venda.id)

            agora = datetime.now(UTC)
            if venda.esta_expirada(agora):
                await self._cancelar_reserva_expirada(uow, venda, agora)
                raise ReservaExpiradaError(venda.id)

            venda.efetivar(agora)
            veiculo = await uow.veiculos.obter_por_id(venda.veiculo_id)
            if veiculo is None:
                raise VeiculoNaoEncontradoError(venda.veiculo_id)
            veiculo.marcar_como_vendido()

            await uow.vendas.atualizar(venda)
            await uow.veiculos.atualizar(veiculo)
            await uow.commit()
            return ReciboVendaDTO.de_venda(venda)

    @staticmethod
    async def _cancelar_reserva_expirada(uow: UnitOfWork, venda: Venda, agora: datetime) -> None:
        """Cancela a venda expirada e libera o veiculo na mesma transacao.

        O commit acontece AQUI, antes de `ReservaExpiradaError` ser levantada
        pelo chamador: o `__aexit__` da unidade de trabalho faz rollback quando
        uma excecao escapa do bloco, e o cancelamento precisa persistir.

        Args:
            uow: Unidade de trabalho em curso.
            venda: Venda PENDENTE com reserva vencida.
            agora: Momento de referencia do cancelamento.
        """
        venda.cancelar(agora)
        veiculo = await uow.veiculos.obter_por_id(venda.veiculo_id)
        if veiculo is not None:
            veiculo.liberar_reserva()
            await uow.veiculos.atualizar(veiculo)
        await uow.vendas.atualizar(venda)
        await uow.commit()
