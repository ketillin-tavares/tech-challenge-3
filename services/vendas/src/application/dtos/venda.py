"""Comandos e DTOs de saida do contexto de Venda."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from src.domain.entities import Venda
from src.domain.value_objects import StatusVenda


class IniciarCompraRequest(BaseModel):
    """Corpo da requisicao de compra (o `cliente_id` vem do JWT, nunca do body)."""

    veiculo_id: UUID


class IniciarCompraCommand(BaseModel):
    """Dados de entrada para iniciar uma compra (reserva do veiculo).

    O `cliente_id` e derivado do `sub` do JWT pelo controller e NUNCA
    aceito a partir do corpo da requisicao.
    """

    veiculo_id: UUID
    cliente_id: str


class TransicaoCompraCommand(BaseModel):
    """Dados de entrada das transicoes/consultas sobre uma venda existente.

    Usado por efetivar, cancelar e obter. O par `cliente_id`/`eh_admin` vem do
    JWT (controller) e decide a autorizacao: dono da venda ou administrador.
    """

    venda_id: UUID
    cliente_id: str
    eh_admin: bool = False


class ReciboVendaDTO(BaseModel):
    """Recibo de uma venda em qualquer ponto do ciclo de vida.

    Centrado na venda: identifica a venda, o veiculo, o comprador, o snapshot
    de preco e o estado atual. `data_venda` so e preenchida apos a efetivacao;
    `expira_em` indica a validade da reserva enquanto PENDENTE.
    """

    id: UUID
    veiculo_id: UUID
    cliente_id: str
    preco_venda: Decimal
    status: StatusVenda
    expira_em: datetime | None
    data_venda: datetime | None

    @classmethod
    def de_venda(cls, venda: Venda) -> "ReciboVendaDTO":
        """Converte um registro de `Venda` em recibo de saida.

        Args:
            venda: Registro da venda.

        Returns:
            DTO de recibo com os dados da venda em tipos primitivos.
        """
        return cls(
            id=venda.id,
            veiculo_id=venda.veiculo_id,
            cliente_id=venda.cliente_id,
            preco_venda=venda.preco_venda.valor,
            status=venda.status,
            expira_em=venda.expira_em,
            data_venda=venda.data_venda,
        )
