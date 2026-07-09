"""Port: repositorio de vendas (write-side)."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import Venda


class VendaRepository(ABC):
    """Contrato de persistencia de vendas."""

    @abstractmethod
    async def adicionar(self, venda: Venda) -> None:
        """Persiste uma nova venda."""
        ...

    @abstractmethod
    async def obter_por_veiculo(self, veiculo_id: UUID) -> Venda | None:
        """Retorna a venda associada a um veiculo, ou None."""
        ...
