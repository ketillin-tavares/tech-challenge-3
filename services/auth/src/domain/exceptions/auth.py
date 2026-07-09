"""Excecoes de dominio do contexto de Identidade/Auth."""

from src.domain.exceptions.base import DomainError


class AuthError(DomainError):
    """Erro base do contexto de autenticacao/identidade."""


class CredenciaisInvalidasError(AuthError):
    """E-mail ou senha invalidos na autenticacao."""

    def __init__(self) -> None:
        """Inicializa com mensagem generica (nao revela qual campo falhou)."""
        super().__init__("Credenciais invalidas.")


class ClienteJaExisteError(AuthError):
    """Tentativa de registrar um e-mail ja existente."""

    def __init__(self, email: str) -> None:
        """Inicializa o erro com o e-mail em conflito.

        Args:
            email: E-mail que ja possui cadastro.
        """
        self.email = email
        super().__init__(f"Ja existe um cliente com o e-mail {email}.")
