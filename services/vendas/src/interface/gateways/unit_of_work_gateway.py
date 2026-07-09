"""Gateway de unidade de trabalho (SQLAlchemy)."""

from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.repositories.unit_of_work import UnitOfWork
from src.interface.gateways.veiculo_repository_gateway import VeiculoRepositoryGateway
from src.interface.gateways.venda_repository_gateway import VendaRepositoryGateway


class UnitOfWorkGateway(UnitOfWork):
    """Coordena uma transacao atomica sobre uma unica `AsyncSession`.

    Cria a sessao no `__aenter__` e expoe os repositorios ligados a ela, de
    modo que `vendas.adicionar` + `veiculos.atualizar` ocorram na mesma
    transacao. O commit e explicito (via `commit()`); o rollback ocorre no
    `__aexit__` quando uma excecao escapa do bloco.
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        """Recebe a fabrica de sessoes.

        Args:
            session_factory: Fabrica de sessoes async do banco.
        """
        self._session_factory = session_factory
        self._session: AsyncSession

    async def __aenter__(self) -> "UnitOfWorkGateway":
        """Abre a sessao/transacao e vincula os repositorios."""
        self._session = self._session_factory()
        self.veiculos = VeiculoRepositoryGateway(self._session)
        self.vendas = VendaRepositoryGateway(self._session)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Faz rollback em caso de excecao e sempre fecha a sessao."""
        if exc_type is not None:
            await self._session.rollback()
        await self._session.close()

    async def commit(self) -> None:
        """Confirma as alteracoes da transacao."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Desfaz as alteracoes da transacao."""
        await self._session.rollback()
