"""Excecao de dominio da validacao de token (mesmo padrao do servico de vendas)."""

from src.domain.exceptions.base import DomainError


class TokenInvalidoError(DomainError):
    """Token JWT ausente, malformado, expirado ou com assinatura invalida."""

    def __init__(self) -> None:
        """Inicializa com mensagem generica de token invalido."""
        super().__init__("Token de autenticacao invalido.")
