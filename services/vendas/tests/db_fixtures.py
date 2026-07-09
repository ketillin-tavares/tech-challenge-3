"""Fixtures compartilhadas para testes de integracao (Testcontainers + Postgres).

Fornece um container ephemero de PostgreSQL e as sessoes async ligadas a ele.
Trunca as tabelas antes/depois de cada teste para garantir isolamento.
"""

from collections.abc import AsyncGenerator, Iterator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from src.infrastructure.models import Base


@pytest.fixture(scope="session")
def postgres_container() -> Iterator[PostgresContainer]:
    """Fornece um container PostgreSQL efemero (escopo de sessao).

    Se Docker nao estiver disponivel, pula todos os testes de integracao.

    Yields:
        Container PostgreSQL ligado.
    """
    try:
        container = PostgresContainer("postgres:16-alpine")
        container.start()
        yield container
        container.stop()
    except Exception as e:
        pytest.skip(f"Docker indisponivel: {e}", allow_module_level=True)


@pytest.fixture(scope="session")
def container_db_url(postgres_container: PostgresContainer) -> str:
    """Fornece a URL de conexao async do container (escopo de sessao).

    Args:
        postgres_container: Container PostgreSQL provisionado.

    Returns:
        String de conexao asyncpg para SQLAlchemy.
    """
    url = postgres_container.get_connection_url(driver="asyncpg")
    return url


@pytest.fixture
async def async_engine(container_db_url: str) -> AsyncGenerator[AsyncEngine]:
    """Fornece um engine async efemero (function-scoped).

    Cria as tabelas via `Base.metadata.create_all` (sem Alembic).
    O engine usa NullPool para evitar conflitos de event loop com pytest-asyncio.

    Args:
        container_db_url: URL do container.

    Yields:
        Engine async configurado e com tabelas criadas.
    """
    engine = create_async_engine(
        container_db_url,
        poolclass=NullPool,
        echo=False,
    )

    # Cria as tabelas no setup.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Descarta o engine no teardown.
    await engine.dispose()


@pytest.fixture
def session_factory(async_engine: AsyncEngine):
    """Fornece uma fabrica de sessoes async (function-scoped).

    Args:
        async_engine: Engine async do container.

    Returns:
        Fabrica async_sessionmaker.
    """
    from sqlalchemy.ext.asyncio import async_sessionmaker

    return async_sessionmaker(async_engine, expire_on_commit=False)


@pytest.fixture
async def db_session(
    session_factory,
) -> AsyncGenerator[AsyncSession]:
    """Fornece uma sessao async individual (function-scoped).

    Args:
        session_factory: Fabrica de sessoes.

    Yields:
        Sessao async aberta.
    """
    async with session_factory() as session:
        yield session


@pytest.fixture
async def _truncate_tables(db_session: AsyncSession) -> None:
    """Trunca as tabelas para isolar o teste (limpa estado antes de cada um).

    Nao e autouse aqui de proposito: os conftests de `tests/integration/` e
    `tests/e2e/` a ativam via um wrapper autouse, garantindo que os testes
    UNIT (que nao tocam o container) permanecam Docker-free.

    O `lock_timeout` evita que uma eventual conexao vazada com transacao aberta
    trave o TRUNCATE (ACCESS EXCLUSIVE) indefinidamente: falha rapido em vez de
    pendurar a suite.

    Args:
        db_session: Sessao async para execucao do TRUNCATE.
    """
    await db_session.execute(text("SET lock_timeout = '5s'"))
    await db_session.execute(text("TRUNCATE TABLE vendas, veiculos RESTART IDENTITY CASCADE"))
    await db_session.commit()
