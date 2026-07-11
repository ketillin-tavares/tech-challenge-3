"""Caso de uso: expirar reservas vencidas (varredura em lote)."""

from datetime import UTC, datetime

from src.application.dtos import ReciboVendaDTO
from src.domain.repositories import UnitOfWork


class ExpirarReservasVencidas:
    """Cancela em lote as vendas PENDENTE com reserva vencida.

    Para cada venda expirada, transita a venda para CANCELADA e devolve o
    veiculo a DISPONIVEL na mesma transacao. Complementa a expiracao lazy do
    `EfetivarCompra`: garante que o estoque nao fica preso em RESERVADO quando
    o cliente simplesmente abandona a compra.
    """

    def __init__(self, uow: UnitOfWork, limite: int = 100) -> None:
        """Recebe a unidade de trabalho e o tamanho do lote por injecao.

        Args:
            uow: Unidade de trabalho que coordena a transacao atomica.
            limite: Maximo de vendas processadas por execucao.
        """
        self._uow = uow
        self._limite = limite

    async def executar(self) -> list[ReciboVendaDTO]:
        """Cancela as reservas vencidas encontradas no lote.

        Returns:
            Recibos das vendas canceladas nesta execucao (vazio se nenhuma).
        """
        async with self._uow as uow:
            agora = datetime.now(UTC)
            vendas = await uow.vendas.listar_pendentes_expiradas(agora, self._limite)
            for venda in vendas:
                venda.cancelar(agora)
                veiculo = await uow.veiculos.obter_por_id(venda.veiculo_id)
                if veiculo is not None:
                    veiculo.liberar_reserva()
                    await uow.veiculos.atualizar(veiculo)
                await uow.vendas.atualizar(venda)
            if vendas:
                await uow.commit()
            return [ReciboVendaDTO.de_venda(venda) for venda in vendas]
