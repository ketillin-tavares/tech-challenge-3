"""Fixtures compartilhadas da suite de testes.

Garante um conjunto minimo de variaveis de ambiente sinteticas para que
`src.environment.get_settings()` resolva sem depender de configuracao real.

As envs sao aplicadas no NIVEL DE MODULO (antes de qualquer import de `src`),
porque modulos de infraestrutura (ex.: `database/session.py`) chamam
`get_settings()` em tempo de import. Assim `uv run pytest` funciona sem nenhum
`export` no shell. `setdefault` preserva qualquer env real ja definida. A
fixture autouse reforca o isolamento por teste e limpa o cache do settings.
"""

import os
from collections.abc import Iterator

_TEST_ENV: dict[str, str] = {
    "DATABASE_URL": "postgresql+asyncpg://test:test@localhost:5432/test",
    "COGNITO_CLIENT_ID": "testclientid",
    "COGNITO_ISSUER": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test000",
    "JWKS_URL": "",
    "ENVIRONMENT": "development",
    "LOG_LEVEL": "INFO",
}

# Aplica as envs ANTES de qualquer import de `src` (env real definida vence).
for _chave, _valor in _TEST_ENV.items():
    os.environ.setdefault(_chave, _valor)

import pytest  # noqa: E402

from src.environment import get_settings  # noqa: E402

# Registra o modulo de fixtures compartilhado para testes de integracao
pytest_plugins = ["tests.db_fixtures"]


@pytest.fixture(autouse=True)
def settings_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Reforca as envs de teste e isola o cache de settings por teste.

    Args:
        monkeypatch: Fixture do pytest para alterar o ambiente de forma isolada.

    Yields:
        None. O cache de `get_settings` e limpo antes e depois de cada teste.
    """
    for chave, valor in _TEST_ENV.items():
        monkeypatch.setenv(chave, valor)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
