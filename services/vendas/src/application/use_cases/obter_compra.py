"""Caso de uso: consultar uma compra (estado atual da venda)."""

from src.application.dtos import ReciboVendaDTO, TransicaoCompraCommand
from src.application.use_cases.acesso_venda import verificar_acesso_venda
from src.domain.repositories import UnitOfWork


class ObterCompra:
    """Consulta o recibo de uma venda pelo dono (ou por um admin).

    Permite ao frontend acompanhar o ciclo de vida da compra (PENDENTE ->
    PAGA/CANCELADA) apos inicia-la.
    """

    def __init__(self, uow: UnitOfWork) -> None:
        """Recebe a unidade de trabalho por injecao.

        Args:
            uow: Unidade de trabalho (usada apenas para leitura).
        """
        self._uow = uow

    async def executar(self, comando: TransicaoCompraCommand) -> ReciboVendaDTO:
        """Retorna o recibo da venda do cliente autenticado (ou admin).

        Args:
            comando: Venda alvo e identidade do solicitante (sub/admin).

        Returns:
            Recibo com o estado atual da venda.

        Raises:
            VendaNaoEncontradaError: Se a venda nao existe ou e de outro cliente.
        """
        async with self._uow as uow:
            venda = verificar_acesso_venda(await uow.vendas.obter_por_id(comando.venda_id), comando)
            return ReciboVendaDTO.de_venda(venda)
