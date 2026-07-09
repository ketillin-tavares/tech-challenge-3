"""Caso de uso: comprar (efetivar a venda de) um veiculo."""

from datetime import UTC, datetime
from uuid import uuid4

from src.application.dtos import ComprarVeiculoCommand, ReciboVendaDTO
from src.domain.entities import Venda
from src.domain.exceptions import VeiculoNaoEncontradoError
from src.domain.repositories import UnitOfWork


class ComprarVeiculo:
    """Efetiva a compra de um veiculo de forma atomica.

    Registra a `Venda` (com snapshot do preco atual) e transita o veiculo para
    VENDIDO na mesma transacao (UnitOfWork).
    """

    def __init__(self, uow: UnitOfWork) -> None:
        """Recebe a unidade de trabalho por injecao.

        Args:
            uow: Unidade de trabalho que coordena a transacao atomica.
        """
        self._uow = uow

    async def executar(self, comando: ComprarVeiculoCommand) -> ReciboVendaDTO:
        """Compra um veiculo disponivel.

        O rollback em caso de erro e responsabilidade do `__aexit__` da
        unidade de trabalho; nenhuma chamada manual de rollback e feita aqui.

        Args:
            comando: Veiculo alvo e identificador do cliente (sub do JWT).

        Returns:
            Recibo da venda efetivada.

        Raises:
            VeiculoNaoEncontradoError: Se o veiculo nao existir.
            VeiculoIndisponivelError: Se o veiculo nao estiver disponivel
                (em memoria ou por violacao de unicidade traduzida no adapter).
        """
        async with self._uow as uow:
            veiculo = await uow.veiculos.obter_por_id(comando.veiculo_id)
            if veiculo is None:
                raise VeiculoNaoEncontradoError(comando.veiculo_id)

            veiculo.marcar_como_vendido()
            agora = datetime.now(UTC)
            venda = Venda(
                id=uuid4(),
                veiculo_id=veiculo.id,
                cliente_id=comando.cliente_id,
                preco_venda=veiculo.preco,
                data_venda=agora,
                created_at=agora,
            )
            await uow.vendas.adicionar(venda)
            await uow.veiculos.atualizar(veiculo)
            await uow.commit()
            return ReciboVendaDTO.de_venda(venda)
