"""Ambiente de migracoes do Alembic (async).

Le a DSN async das settings e usa `create_async_engine`. O `target_metadata`
vem do barrel de models (registra todas as tabelas para autogeracao).
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from src.environment import get_settings
from src.infrastructure.models import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata
_DATABASE_URL = get_settings().database.url


def run_migrations_offline() -> None:
    """Executa as migracoes em modo offline (gera SQL, sem conectar)."""
    context.configure(
        url=_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Configura o contexto com a conexao e roda as migracoes."""
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Abre uma conexao async e executa as migracoes."""
    engine = create_async_engine(_DATABASE_URL)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_online() -> None:
    """Executa as migracoes em modo online (conexao async real)."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
