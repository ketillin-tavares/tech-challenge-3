"""Value Object StatusVeiculo."""

from enum import StrEnum


class StatusVeiculo(StrEnum):
    """Estado de um veiculo no ciclo de venda."""

    DISPONIVEL = "DISPONIVEL"
    VENDIDO = "VENDIDO"
