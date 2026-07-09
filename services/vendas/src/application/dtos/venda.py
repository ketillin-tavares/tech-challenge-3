"""Comandos e DTOs de saida do contexto de Venda."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities import Venda


class ComprarVeiculoRequest(BaseModel):
    """Corpo da requisicao de compra (o `cliente_id` vem do JWT, nunca do body)."""

    veiculo_id: UUID


class ComprarVeiculoCommand(BaseModel):
    """Dados de entrada para efetivar uma compra.

    O `cliente_id` e derivado do `sub` do JWT pelo controller (T4) e NUNCA
    aceito a partir do corpo da requisicao.
    """

    veiculo_id: UUID
    cliente_id: str


class ReciboVendaDTO(BaseModel):
    """Recibo de uma venda efetivada (resposta da compra).

    Centrado na venda: identifica a venda, o veiculo, o comprador e o snapshot
    de preco/data.
    """

    id: UUID
    veiculo_id: UUID
    cliente_id: str
    preco_venda: Decimal
    data_venda: datetime

    @classmethod
    def de_venda(cls, venda: Venda) -> "ReciboVendaDTO":
        """Converte um registro de `Venda` em recibo de saida.

        Args:
            venda: Registro da venda efetivada.

        Returns:
            DTO de recibo com os dados da venda em tipos primitivos.
        """
        return cls(
            id=venda.id,
            veiculo_id=venda.veiculo_id,
            cliente_id=venda.cliente_id,
            preco_venda=venda.preco_venda.valor,
            data_venda=venda.data_venda,
        )
