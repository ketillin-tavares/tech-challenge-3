"""Excecoes de dominio do servico de auth."""

from src.domain.exceptions.auth import (
    AuthError,
    ClienteJaExisteError,
    CredenciaisInvalidasError,
)
from src.domain.exceptions.base import DomainError

__all__ = [
    "AuthError",
    "ClienteJaExisteError",
    "CredenciaisInvalidasError",
    "DomainError",
]
