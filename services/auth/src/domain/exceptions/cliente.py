"""Excecoes de dominio do contexto de Perfil de Cliente.

Politica de PII: as mensagens sao FIXAS (sem interpolacao de CPF/email) --
o handler da borda devolve `str(exc)` no envelope e loga a mensagem, entao
qualquer PII interpolada vazaria para resposta HTTP e logs.
"""

from src.domain.exceptions.base import DomainError


class ClienteNaoEncontradoError(DomainError):
    """Perfil de cliente inexistente para o identificador informado."""

    def __init__(self) -> None:
        """Inicializa com mensagem fixa (sem expor identificadores)."""
        super().__init__("Cliente nao encontrado.")
