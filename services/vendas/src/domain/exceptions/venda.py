"""Excecoes de dominio do contexto de Venda (ciclo compra -> efetivacao)."""

from uuid import UUID

from src.domain.exceptions.base import DomainError


class VendaNaoEncontradaError(DomainError):
    """Venda inexistente para o identificador informado.

    Tambem usada quando a venda pertence a outro cliente (a existencia nao e
    revelada para evitar enumeracao de identificadores).
    """

    def __init__(self, venda_id: UUID) -> None:
        """Inicializa o erro com o identificador procurado.

        Args:
            venda_id: Identificador da venda nao encontrada.
        """
        self.venda_id = venda_id
        super().__init__(f"Venda {venda_id} nao encontrada.")


class TransicaoVendaInvalidaError(DomainError):
    """Transicao de estado invalida para a venda (ex.: efetivar CANCELADA)."""

    def __init__(self, venda_id: UUID) -> None:
        """Inicializa o erro com o identificador da venda afetada.

        Args:
            venda_id: Identificador da venda cuja transicao foi rejeitada.
        """
        self.venda_id = venda_id
        super().__init__(f"Transicao de estado invalida para a venda {venda_id}.")


class ReservaExpiradaError(DomainError):
    """Tentativa de efetivar uma venda cuja reserva ja expirou."""

    def __init__(self, venda_id: UUID) -> None:
        """Inicializa o erro com o identificador da venda afetada.

        Args:
            venda_id: Identificador da venda com reserva expirada.
        """
        self.venda_id = venda_id
        super().__init__(f"Reserva da venda {venda_id} expirou.")


class ReservaAtivaExistenteError(DomainError):
    """Cliente ja possui uma venda PENDENTE (limite de 1 reserva ativa)."""

    def __init__(self) -> None:
        """Inicializa com mensagem fixa (sem expor identificadores)."""
        super().__init__("Ja existe uma compra pendente para este cliente.")
