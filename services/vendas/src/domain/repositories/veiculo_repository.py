"""Port: repositorio de veiculos (write-side)."""

from abc import ABC, abstractmethod
from uuid import UUID

from src.domain.entities import Veiculo
from src.domain.value_objects import StatusVeiculo


class VeiculoRepository(ABC):
    """Contrato de persistencia de veiculos."""

    @abstractmethod
    async def adicionar(self, veiculo: Veiculo) -> None:
        """Persiste um novo veiculo."""
        ...

    @abstractmethod
    async def obter_por_id(self, veiculo_id: UUID) -> Veiculo | None:
        """Retorna o veiculo pelo id, ou None se inexistente."""
        ...

    @abstractmethod
    async def listar_por_status(
        self,
        status: StatusVeiculo,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Veiculo]:
        """Lista veiculos de um status, ordenados por preco ascendente (paginado)."""
        ...

    @abstractmethod
    async def atualizar(self, veiculo: Veiculo) -> None:
        """Persiste alteracoes de um veiculo existente."""
        ...
