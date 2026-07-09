"""Port de leitura: servico de consultas de veiculos (read-model)."""

from abc import ABC, abstractmethod

from src.application.dtos import VeiculoDTO, VeiculoVendidoDTO


class VeiculoQueryService(ABC):
    """Consultas de leitura sobre veiculos (CQRS - lado de leitura)."""

    @abstractmethod
    async def listar_disponiveis(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[VeiculoDTO]:
        """Lista veiculos DISPONIVEIS, ordenados por preco ascendente (paginado)."""
        ...

    @abstractmethod
    async def listar_vendidos(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[VeiculoVendidoDTO]:
        """Lista veiculos VENDIDOS com os dados da venda, por preco asc (paginado)."""
        ...
