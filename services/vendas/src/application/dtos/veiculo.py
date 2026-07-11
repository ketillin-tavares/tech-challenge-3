"""Comandos e DTOs de saida do contexto de Veiculo.

Os comandos carregam apenas primitivos (a fronteira da aplicacao nao expoe
Value Objects de dominio). Os DTOs de saida tambem expoem primitivos, evitando
que entidades/VOs vazem para a camada de adapters. Os VOs sao construidos
dentro dos use cases; uma `pydantic.ValidationError` ai resultante propaga ate
a borda (traduzida para 422).
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from src.domain.entities import Veiculo, Venda
from src.domain.value_objects import StatusVeiculo


class CadastrarVeiculoCommand(BaseModel):
    """Dados de entrada para cadastrar um veiculo (corpo da requisicao)."""

    marca: str = Field(min_length=1)
    modelo: str = Field(min_length=1)
    ano: int
    cor: str = Field(min_length=1)
    preco: Decimal


class EditarVeiculoRequest(BaseModel):
    """Corpo da requisicao de edicao de veiculo (o id vem do path)."""

    marca: str = Field(min_length=1)
    modelo: str = Field(min_length=1)
    ano: int
    cor: str = Field(min_length=1)
    preco: Decimal


class EditarVeiculoCommand(BaseModel):
    """Dados de entrada para a edicao total de um veiculo."""

    veiculo_id: UUID
    marca: str
    modelo: str
    ano: int
    cor: str
    preco: Decimal


class VeiculoDTO(BaseModel):
    """Representacao de saida de um veiculo (primitivos)."""

    id: UUID
    marca: str
    modelo: str
    ano: int
    cor: str
    preco: Decimal
    status: StatusVeiculo
    created_at: datetime
    updated_at: datetime

    @classmethod
    def de_entidade(cls, veiculo: Veiculo) -> "VeiculoDTO":
        """Converte uma entidade `Veiculo` em DTO de saida.

        Args:
            veiculo: Entidade de dominio.

        Returns:
            DTO com os campos do veiculo em tipos primitivos.
        """
        return cls(
            id=veiculo.id,
            marca=veiculo.marca,
            modelo=veiculo.modelo,
            ano=veiculo.ano.valor,
            cor=veiculo.cor,
            preco=veiculo.preco.valor,
            status=veiculo.status,
            created_at=veiculo.created_at,
            updated_at=veiculo.updated_at,
        )


class VeiculoVendidoDTO(VeiculoDTO):
    """Veiculo vendido enriquecido com os dados da venda associada."""

    preco_venda: Decimal
    data_venda: datetime

    @classmethod
    def de_entidades(cls, veiculo: Veiculo, venda: Venda) -> "VeiculoVendidoDTO":
        """Combina veiculo e venda em um DTO de leitura.

        Args:
            veiculo: Entidade do veiculo vendido.
            venda: Registro da venda EFETIVADA (PAGA) associada.

        Returns:
            DTO com os dados do veiculo e da venda (snapshot).

        Raises:
            ValueError: Se a venda nao tiver `data_venda` (apenas vendas
                efetivadas compoem o veiculo vendido).
        """
        if venda.data_venda is None:
            raise ValueError("Apenas vendas efetivadas (PAGA) compoem o veiculo vendido.")
        return cls(
            **VeiculoDTO.de_entidade(veiculo).model_dump(),
            preco_venda=venda.preco_venda.valor,
            data_venda=venda.data_venda,
        )
