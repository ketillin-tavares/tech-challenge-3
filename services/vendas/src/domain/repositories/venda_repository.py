"""Port: repositorio de vendas (write-side)."""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from src.domain.entities import Venda


class VendaRepository(ABC):
    """Contrato de persistencia de vendas."""

    @abstractmethod
    async def adicionar(self, venda: Venda) -> None:
        """Persiste uma nova venda."""
        ...

    @abstractmethod
    async def obter_por_id(self, venda_id: UUID) -> Venda | None:
        """Retorna a venda pelo id, ou None se inexistente."""
        ...

    @abstractmethod
    async def obter_por_veiculo(self, veiculo_id: UUID) -> Venda | None:
        """Retorna a venda associada a um veiculo, ou None."""
        ...

    @abstractmethod
    async def obter_pendente_por_cliente(self, cliente_id: str) -> Venda | None:
        """Retorna a venda PENDENTE do cliente, ou None se nao houver."""
        ...

    @abstractmethod
    async def listar_pendentes_expiradas(self, agora: datetime, limite: int) -> list[Venda]:
        """Lista vendas PENDENTE com `expira_em` vencido (lote da varredura)."""
        ...

    @abstractmethod
    async def atualizar(self, venda: Venda) -> None:
        """Persiste alteracoes de uma venda existente."""
        ...
