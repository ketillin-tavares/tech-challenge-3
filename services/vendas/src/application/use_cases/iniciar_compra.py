"""Caso de uso: iniciar a compra de um veiculo (reserva com prazo)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from src.application.dtos import IniciarCompraCommand, ReciboVendaDTO
from src.domain.entities import Venda
from src.domain.exceptions import ReservaAtivaExistenteError, VeiculoNaoEncontradoError
from src.domain.repositories import UnitOfWork


class IniciarCompra:
    """Inicia a compra de um veiculo de forma atomica.

    Registra a `Venda` PENDENTE (com snapshot do preco atual e prazo de
    reserva) e transita o veiculo para RESERVADO na mesma transacao
    (UnitOfWork). A efetivacao e o cancelamento sao casos de uso proprios.
    """

    def __init__(self, uow: UnitOfWork, reserva_ttl: timedelta) -> None:
        """Recebe a unidade de trabalho e o prazo de reserva por injecao.

        Args:
            uow: Unidade de trabalho que coordena a transacao atomica.
            reserva_ttl: Validade da reserva (define `expira_em` da venda).
        """
        self._uow = uow
        self._reserva_ttl = reserva_ttl

    async def executar(self, comando: IniciarCompraCommand) -> ReciboVendaDTO:
        """Reserva um veiculo disponivel para o cliente.

        Cada cliente pode ter no maximo UMA venda PENDENTE (anti-abuso de
        reservas): a pre-checagem produz o erro amigavel e o indice unico
        parcial do banco garante a regra sob concorrencia (traduzido no
        adapter). O rollback em caso de erro e responsabilidade do
        `__aexit__` da unidade de trabalho.

        Args:
            comando: Veiculo alvo e identificador do cliente (sub do JWT).

        Returns:
            Recibo da venda PENDENTE criada (com `expira_em`).

        Raises:
            ReservaAtivaExistenteError: Se o cliente ja possui venda PENDENTE.
            VeiculoNaoEncontradoError: Se o veiculo nao existir.
            VeiculoIndisponivelError: Se o veiculo nao estiver disponivel
                (em memoria ou por violacao de unicidade traduzida no adapter).
        """
        async with self._uow as uow:
            pendente = await uow.vendas.obter_pendente_por_cliente(comando.cliente_id)
            if pendente is not None:
                raise ReservaAtivaExistenteError

            veiculo = await uow.veiculos.obter_por_id(comando.veiculo_id)
            if veiculo is None:
                raise VeiculoNaoEncontradoError(comando.veiculo_id)

            veiculo.reservar()
            agora = datetime.now(UTC)
            venda = Venda(
                id=uuid4(),
                veiculo_id=veiculo.id,
                cliente_id=comando.cliente_id,
                preco_venda=veiculo.preco,
                expira_em=agora + self._reserva_ttl,
                created_at=agora,
                updated_at=agora,
            )
            await uow.vendas.adicionar(venda)
            await uow.veiculos.atualizar(veiculo)
            await uow.commit()
            return ReciboVendaDTO.de_venda(venda)
