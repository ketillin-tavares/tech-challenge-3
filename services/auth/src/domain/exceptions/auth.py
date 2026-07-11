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
    """Tentativa de registrar dados ja cadastrados (ex.: e-mail existente).

    A mensagem e FIXA e nao revela qual dado colidiu nem o seu valor: o
    handler da borda devolve `str(exc)` no envelope, e PII interpolada
    vazaria para resposta HTTP e logs.
    """

    def __init__(self) -> None:
        """Inicializa com mensagem generica de dados ja cadastrados."""
        super().__init__("Dados ja cadastrados.")
