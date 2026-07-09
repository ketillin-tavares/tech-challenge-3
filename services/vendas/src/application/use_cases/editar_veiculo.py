"""Caso de uso: editar (substituir) os dados de um veiculo."""

from src.application.dtos import EditarVeiculoCommand, VeiculoDTO
from src.domain.exceptions import VeiculoNaoEncontradoError
from src.domain.repositories import VeiculoRepository
from src.domain.value_objects import Ano, Preco


class EditarVeiculo:
    """Substitui os dados cadastrais de um veiculo existente."""

    def __init__(self, repositorio: VeiculoRepository) -> None:
        """Recebe o repositorio de veiculos por injecao.

        Args:
            repositorio: Port de persistencia de veiculos.
        """
        self._repositorio = repositorio

    async def executar(self, comando: EditarVeiculoCommand) -> VeiculoDTO:
        """Edita um veiculo existente (substituicao total).

        Args:
            comando: Identificador e novos dados do veiculo.

        Returns:
            DTO do veiculo atualizado.

        Raises:
            VeiculoNaoEncontradoError: Se o veiculo nao existir.
            VeiculoVendidoNaoEditavelError: Se o veiculo ja estiver vendido.
        """
        veiculo = await self._repositorio.obter_por_id(comando.veiculo_id)
        if veiculo is None:
            raise VeiculoNaoEncontradoError(comando.veiculo_id)

        veiculo.atualizar_dados(
            marca=comando.marca,
            modelo=comando.modelo,
            ano=Ano(valor=comando.ano),
            cor=comando.cor,
            preco=Preco(valor=comando.preco),
        )
        await self._repositorio.atualizar(veiculo)
        return VeiculoDTO.de_entidade(veiculo)
