"""Tarefas de background da aplicacao (asyncio, sem broker externo)."""

from src.infrastructure.tasks.expiracao_reservas import executar_loop_expiracao

__all__ = ["executar_loop_expiracao"]
