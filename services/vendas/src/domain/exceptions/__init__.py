"""Excecoes de dominio do servico de vendas."""

from src.domain.exceptions.base import DomainError
from src.domain.exceptions.token import TokenInvalidoError
from src.domain.exceptions.veiculo import (
    VeiculoIndisponivelError,
    VeiculoNaoEncontradoError,
    VeiculoVendidoNaoEditavelError,
)
from src.domain.exceptions.venda import (
    ReservaAtivaExistenteError,
    ReservaExpiradaError,
    TransicaoVendaInvalidaError,
    VendaNaoEncontradaError,
)

__all__ = [
    "DomainError",
    "ReservaAtivaExistenteError",
    "ReservaExpiradaError",
    "TokenInvalidoError",
    "TransicaoVendaInvalidaError",
    "VeiculoIndisponivelError",
    "VeiculoNaoEncontradoError",
    "VeiculoVendidoNaoEditavelError",
    "VendaNaoEncontradaError",
]
