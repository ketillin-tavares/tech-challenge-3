"""Value Object StatusVeiculo."""

from enum import StrEnum


class StatusVeiculo(StrEnum):
    """Estado de um veiculo no ciclo de venda.

    DISPONIVEL -> RESERVADO (compra iniciada) -> VENDIDO (compra efetivada).
    O cancelamento ou a expiracao da reserva devolve o veiculo a DISPONIVEL.
    """

    DISPONIVEL = "DISPONIVEL"
    RESERVADO = "RESERVADO"
    VENDIDO = "VENDIDO"
