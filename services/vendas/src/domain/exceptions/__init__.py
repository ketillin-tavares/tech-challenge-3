"""Excecoes de dominio do servico de vendas."""

from src.domain.exceptions.base import DomainError
from src.domain.exceptions.token import TokenInvalidoError
from src.domain.exceptions.veiculo import (
    VeiculoIndisponivelError,
    VeiculoNaoEncontradoError,
    VeiculoVendidoNaoEditavelError,
)

__all__ = [
    "DomainError",
    "TokenInvalidoError",
    "VeiculoIndisponivelError",
    "VeiculoNaoEncontradoError",
    "VeiculoVendidoNaoEditavelError",
]
