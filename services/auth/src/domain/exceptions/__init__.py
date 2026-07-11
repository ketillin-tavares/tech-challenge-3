"""Excecoes de dominio do servico de auth."""

from src.domain.exceptions.auth import (
    AuthError,
    ClienteJaExisteError,
    CredenciaisInvalidasError,
)
from src.domain.exceptions.base import DomainError
from src.domain.exceptions.cliente import ClienteNaoEncontradoError
from src.domain.exceptions.token import TokenInvalidoError

__all__ = [
    "AuthError",
    "ClienteJaExisteError",
    "ClienteNaoEncontradoError",
    "CredenciaisInvalidasError",
    "DomainError",
    "TokenInvalidoError",
]
