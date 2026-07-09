"""Configuracao de pytest para testes E2E.

Fornece fixtures de app/client com sobrescrita de dependencias para usar
o container Postgres. As fixtures de DB sao registradas no top-level conftest.
"""

from collections.abc import AsyncGenerator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.ports.token_verifier import TokenVerifier
from src.domain.value_objects import ClienteAutenticado
from src.infrastructure.database.session import get_session
from src.interface.controllers.dependencies import get_token_verifier


@pytest.fixture(autouse=True)
async def _auto_truncate(_truncate_tables: None) -> None:
    """Aplica o truncate de isolamento a todos os testes E2E."""
    return None


class FakeTokenVerifier(TokenVerifier):
    """Verificador de token fake: devolve uma identidade pre-definida."""

    def __init__(self, sub: str = "cliente-test", grupos: tuple[str, ...] = ()) -> None:
        self._cliente = ClienteAutenticado(sub=sub, grupos=grupos)

    def verificar(self, token: str) -> ClienteAutenticado:
        return self._cliente


@pytest.fixture
async def app_with_container(
    session_factory: async_sessionmaker[AsyncSession],
) -> FastAPI:
    """Fornece a aplicacao FastAPI com dependencias sobrescritas para o container.

    Args:
        session_factory: Fabrica de sessoes do container.

    Returns:
        Instancia FastAPI com overrides de dependencias.
    """
    from src.main import create_app

    app = create_app()

    # Override de get_session: usa a sessao do container.
    async def get_container_session() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = get_container_session

    # Override de get_token_verifier: usa o fake.
    app.dependency_overrides[get_token_verifier] = lambda: FakeTokenVerifier(
        sub="cliente-e2e",
        grupos=("admin",),
    )

    return app


@pytest.fixture
def client_with_container(app_with_container: FastAPI) -> TestClient:
    """Fornece um TestClient com app sobrescrita.

    Args:
        app_with_container: App com overrides.

    Returns:
        TestClient funcional.
    """
    return TestClient(app_with_container)
