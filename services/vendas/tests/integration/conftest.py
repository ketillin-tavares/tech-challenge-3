"""Configuracao de pytest para testes de integracao (Testcontainers).

As fixtures de banco sao registradas no top-level conftest via pytest_plugins
(`tests.db_fixtures`). Aqui apenas ativamos o truncate de isolamento como
autouse, restrito a este subdiretorio (os testes unit permanecem Docker-free).
"""

import pytest


@pytest.fixture(autouse=True)
async def _auto_truncate(_truncate_tables: None) -> None:
    """Aplica o truncate de isolamento a todos os testes de integracao."""
    return None
