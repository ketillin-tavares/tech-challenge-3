"""Configuracao de logging estruturado com `loguru` (camada de infraestrutura).

Centraliza a configuracao do logger e o ponto de acesso unico `get_logger()`.
O `print()` e proibido no projeto; toda saida de informacao passa por aqui.

Observacao: a camada de observabilidade (New Relic, metricas, tracing) esta
fora de escopo deste servico -- aqui ha apenas logging.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import Logger


def configure_logging(level: str) -> None:
    """Configura o sink global do `loguru`.

    Remove os handlers padrao e adiciona um sink em ``stderr`` serializado
    (JSON), respeitando o nivel minimo informado.

    Args:
        level: Nivel minimo de log (ex.: ``INFO``, ``DEBUG``).
    """
    logger.remove()
    logger.add(sys.stderr, level=level, serialize=True)


def get_logger() -> Logger:
    """Retorna o logger estruturado da aplicacao.

    Returns:
        Instancia global do logger `loguru` ja configurada.
    """
    return logger
