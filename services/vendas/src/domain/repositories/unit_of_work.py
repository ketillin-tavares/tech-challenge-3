"""Port: unidade de trabalho (transacao atomica)."""

from abc import ABC, abstractmethod
from types import TracebackType

from src.domain.repositories.veiculo_repository import VeiculoRepository
from src.domain.repositories.venda_repository import VendaRepository


class UnitOfWork(ABC):
    """Coordena uma transacao atomica sobre os repositorios.

    Expoe os repositorios participantes e garante commit/rollback atomico.
    Usado pelo caso de uso ComprarVeiculo para registrar a venda e marcar o
    veiculo como vendido na mesma transacao.

    Atributos:
        veiculos: Repositorio de veiculos vinculado a transacao.
        vendas: Repositorio de vendas vinculado a transacao.
    """

    veiculos: VeiculoRepository
    vendas: VendaRepository

    @abstractmethod
    async def __aenter__(self) -> "UnitOfWork":
        """Inicia a transacao e retorna a propria unidade de trabalho."""
        ...

    @abstractmethod
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Finaliza a transacao (rollback automatico em caso de excecao)."""
        ...

    @abstractmethod
    async def commit(self) -> None:
        """Confirma as alteracoes da transacao."""
        ...

    @abstractmethod
    async def rollback(self) -> None:
        """Desfaz as alteracoes da transacao."""
        ...
