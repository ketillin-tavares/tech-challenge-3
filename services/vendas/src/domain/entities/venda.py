"""Entidade Venda."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.exceptions import TransicaoVendaInvalidaError
from src.domain.value_objects import Preco, StatusVenda


class Venda(BaseModel):
    """Registro que liga um veiculo a um cliente, com ciclo de vida proprio.

    A venda nasce PENDENTE (compra iniciada, veiculo reservado) e termina PAGA
    (efetivada) ou CANCELADA (desistencia ou reserva expirada). O `preco_venda`
    e um snapshot do preco do veiculo no momento da reserva. O `cliente_id` e o
    `sub` opaco do JWT (sem PII).

    Atributos:
        id: Identificador unico da venda.
        veiculo_id: Veiculo vendido.
        cliente_id: Identidade opaca do comprador (sub do JWT).
        preco_venda: Snapshot do preco no momento da reserva.
        status: Estado atual; nasce PENDENTE.
        expira_em: Limite de validade da reserva (apenas enquanto PENDENTE).
        data_venda: Momento da efetivacao (preenchida apenas quando PAGA).
        created_at: Momento de criacao do registro.
        updated_at: Momento da ultima alteracao.
    """

    model_config = ConfigDict(validate_assignment=True)

    id: UUID
    veiculo_id: UUID
    cliente_id: str = Field(min_length=1)
    preco_venda: Preco
    status: StatusVenda = StatusVenda.PENDENTE
    expira_em: datetime | None = None
    data_venda: datetime | None = None
    created_at: datetime
    updated_at: datetime

    def efetivar(self, agora: datetime) -> None:
        """Transita a venda de PENDENTE para PAGA (efetivacao da compra).

        Args:
            agora: Momento da efetivacao (vira `data_venda`).

        Raises:
            TransicaoVendaInvalidaError: Se a venda nao estiver PENDENTE.
        """
        if self.status is not StatusVenda.PENDENTE:
            raise TransicaoVendaInvalidaError(self.id)
        self.status = StatusVenda.PAGA
        self.data_venda = agora
        self.updated_at = agora

    def cancelar(self, agora: datetime) -> None:
        """Transita a venda de PENDENTE para CANCELADA (libera a reserva).

        Args:
            agora: Momento do cancelamento.

        Raises:
            TransicaoVendaInvalidaError: Se a venda nao estiver PENDENTE.
        """
        if self.status is not StatusVenda.PENDENTE:
            raise TransicaoVendaInvalidaError(self.id)
        self.status = StatusVenda.CANCELADA
        self.updated_at = agora

    def esta_expirada(self, agora: datetime) -> bool:
        """Indica se a reserva desta venda ja passou do prazo de validade.

        Args:
            agora: Momento de referencia da verificacao.

        Returns:
            True se a venda esta PENDENTE com `expira_em` vencido.
        """
        return (
            self.status is StatusVenda.PENDENTE
            and self.expira_em is not None
            and agora >= self.expira_em
        )
