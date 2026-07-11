"""Comandos de entrada e DTOs de saida da camada de aplicacao."""

from src.application.dtos.paginacao import PaginacaoQuery
from src.application.dtos.veiculo import (
    CadastrarVeiculoCommand,
    EditarVeiculoCommand,
    EditarVeiculoRequest,
    VeiculoDTO,
    VeiculoVendidoDTO,
)
from src.application.dtos.venda import (
    IniciarCompraCommand,
    IniciarCompraRequest,
    ReciboVendaDTO,
    TransicaoCompraCommand,
)

__all__ = [
    "CadastrarVeiculoCommand",
    "EditarVeiculoCommand",
    "EditarVeiculoRequest",
    "IniciarCompraCommand",
    "IniciarCompraRequest",
    "PaginacaoQuery",
    "ReciboVendaDTO",
    "TransicaoCompraCommand",
    "VeiculoDTO",
    "VeiculoVendidoDTO",
]
