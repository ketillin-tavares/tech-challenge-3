"""Caso de uso: cadastrar um novo veiculo."""

from datetime import UTC, datetime
from uuid import uuid4

from src.application.dtos import CadastrarVeiculoCommand, VeiculoDTO
from src.domain.entities import Veiculo
from src.domain.repositories import VeiculoRepository
from src.domain.value_objects import Ano, Preco


class CadastrarVeiculo:
    """Cria um veiculo DISPONIVEL e o persiste."""

    def __init__(self, repositorio: VeiculoRepository) -> None:
        """Recebe o repositorio de veiculos por injecao.

        Args:
            repositorio: Port de persistencia de veiculos.
        """
        self._repositorio = repositorio

    async def executar(self, comando: CadastrarVeiculoCommand) -> VeiculoDTO:
        """Cadastra um novo veiculo.

        Os Value Objects (`Ano`, `Preco`) sao construidos aqui; valores
        invalidos levantam `pydantic.ValidationError`, tratada na borda (422).

        Args:
            comando: Dados do veiculo a cadastrar.

        Returns:
            DTO do veiculo recem-cadastrado.
        """
        agora = datetime.now(UTC)
        veiculo = Veiculo(
            id=uuid4(),
            marca=comando.marca,
            modelo=comando.modelo,
            ano=Ano(valor=comando.ano),
            cor=comando.cor,
            preco=Preco(valor=comando.preco),
            created_at=agora,
            updated_at=agora,
        )
        await self._repositorio.adicionar(veiculo)
        return VeiculoDTO.de_entidade(veiculo)
