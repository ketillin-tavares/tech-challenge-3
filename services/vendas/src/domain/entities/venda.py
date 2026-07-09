"""Entidade Venda."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.value_objects import Preco


class Venda(BaseModel):
    """Registro imutavel que liga um veiculo a um cliente autenticado.

    O `preco_venda` e um snapshot do preco do veiculo no momento da compra.
    O `cliente_id` e o `sub` opaco do JWT (sem PII).

    Atributos:
        id: Identificador unico da venda.
        veiculo_id: Veiculo vendido.
        cliente_id: Identidade opaca do comprador (sub do JWT).
        preco_venda: Snapshot do preco no momento da venda.
        data_venda: Momento da efetivacao da venda.
        created_at: Momento de criacao do registro.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID
    veiculo_id: UUID
    cliente_id: str = Field(min_length=1)
    preco_venda: Preco
    data_venda: datetime
    created_at: datetime
