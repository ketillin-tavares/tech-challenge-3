"""Caso de uso: listar veiculos vendidos."""

from src.application.dtos import PaginacaoQuery, VeiculoVendidoDTO
from src.application.ports import VeiculoQueryService


class ListarVendidos:
    """Lista veiculos VENDIDOS com os dados da venda, por preco ascendente."""

    def __init__(self, consultas: VeiculoQueryService) -> None:
        """Recebe o servico de consultas por injecao.

        Args:
            consultas: Port de leitura (read-model) de veiculos.
        """
        self._consultas = consultas

    async def executar(self, paginacao: PaginacaoQuery) -> list[VeiculoVendidoDTO]:
        """Retorna a lista paginada de veiculos vendidos.

        Args:
            paginacao: Parametros de limite e deslocamento.

        Returns:
            Lista de DTOs de veiculos vendidos (com snapshot da venda).
        """
        return await self._consultas.listar_vendidos(
            limit=paginacao.limit,
            offset=paginacao.offset,
        )
