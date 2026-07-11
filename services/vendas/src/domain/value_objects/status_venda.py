"""Value Object StatusVenda."""

from enum import StrEnum


class StatusVenda(StrEnum):
    """Estado de uma venda no ciclo compra -> efetivacao.

    A venda nasce PENDENTE (veiculo reservado) e termina PAGA (efetivada)
    ou CANCELADA (desistencia ou reserva expirada). Estados terminais nao
    admitem novas transicoes.
    """

    PENDENTE = "PENDENTE"
    PAGA = "PAGA"
    CANCELADA = "CANCELADA"
