"""Engine async, session factory e dependency provider de sessao."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.environment import get_settings

_settings = get_settings()

async_engine = create_async_engine(
    _settings.database.url,
    echo=_settings.app.environment == "development",
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession]:
    """Fornece uma sessao async com commit/rollback automatico.

    Faz commit ao final do request (cobre operacoes de escrita unica como
    cadastrar/editar) e rollback em caso de excecao. Fluxos atomicos
    multi-passo usam a UnitOfWork, que gerencia a propria transacao.

    Yields:
        Sessao assincrona do banco de dados.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
