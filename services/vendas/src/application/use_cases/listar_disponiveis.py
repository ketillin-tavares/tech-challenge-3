"""Caso de uso: listar veiculos disponiveis."""

from src.application.dtos import PaginacaoQuery, VeiculoDTO
from src.application.ports import VeiculoQueryService


class ListarDisponiveis:
    """Lista veiculos DISPONIVEIS, ordenados por preco ascendente."""

    def __init__(self, consultas: VeiculoQueryService) -> None:
        """Recebe o servico de consultas por injecao.

        Args:
            consultas: Port de leitura (read-model) de veiculos.
        """
        self._consultas = consultas

    async def executar(self, paginacao: PaginacaoQuery) -> list[VeiculoDTO]:
        """Retorna a lista paginada de veiculos disponiveis.

        Args:
            paginacao: Parametros de limite e deslocamento.

        Returns:
            Lista de DTOs de veiculos disponiveis.
        """
        return await self._consultas.listar_disponiveis(
            limit=paginacao.limit,
            offset=paginacao.offset,
        )
