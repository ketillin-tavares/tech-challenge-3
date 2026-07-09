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
    ComprarVeiculoCommand,
    ComprarVeiculoRequest,
    ReciboVendaDTO,
)

__all__ = [
    "CadastrarVeiculoCommand",
    "ComprarVeiculoCommand",
    "ComprarVeiculoRequest",
    "EditarVeiculoCommand",
    "EditarVeiculoRequest",
    "PaginacaoQuery",
    "ReciboVendaDTO",
    "VeiculoDTO",
    "VeiculoVendidoDTO",
]
