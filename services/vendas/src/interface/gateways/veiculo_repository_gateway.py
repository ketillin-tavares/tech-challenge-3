"""Gateway de persistencia de veiculos (SQLAlchemy)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Veiculo
from src.domain.repositories.veiculo_repository import VeiculoRepository
from src.domain.value_objects import Ano, Preco, StatusVeiculo
from src.infrastructure.models import VeiculoModel


class VeiculoRepositoryGateway(VeiculoRepository):
    """Adapter que implementa `VeiculoRepository` usando SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Recebe a sessao async do banco.

        Args:
            session: Sessao SQLAlchemy ligada a transacao em curso.
        """
        self._session = session

    async def adicionar(self, veiculo: Veiculo) -> None:
        """Persiste um novo veiculo (commit a cargo do provider/UoW)."""
        self._session.add(self._entity_to_model(veiculo))

    async def obter_por_id(self, veiculo_id: UUID) -> Veiculo | None:
        """Busca um veiculo pelo id (lock pessimista na linha).

        Este metodo so participa de fluxos de escrita (reservar, efetivar,
        cancelar, editar); o `FOR UPDATE` serializa transicoes concorrentes
        sobre o mesmo veiculo. As listagens usam o query service (read-side).
        """
        model = await self._session.get(VeiculoModel, veiculo_id, with_for_update=True)
        return self._model_to_entity(model) if model is not None else None

    async def listar_por_status(
        self,
        status: StatusVeiculo,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Veiculo]:
        """Lista veiculos de um status, ordenados por preco ascendente."""
        stmt = (
            select(VeiculoModel)
            .where(VeiculoModel.status == status.value)
            .order_by(VeiculoModel.preco.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._model_to_entity(model) for model in result.scalars().all()]

    async def atualizar(self, veiculo: Veiculo) -> None:
        """Aplica as alteracoes de um veiculo existente (read-modify-write)."""
        model = await self._session.get(VeiculoModel, veiculo.id)
        if model is None:
            return
        model.marca = veiculo.marca
        model.modelo = veiculo.modelo
        model.ano = veiculo.ano.valor
        model.cor = veiculo.cor
        model.preco = veiculo.preco.valor
        model.status = veiculo.status.value
        model.updated_at = veiculo.updated_at

    @staticmethod
    def _entity_to_model(veiculo: Veiculo) -> VeiculoModel:
        """Converte a entidade `Veiculo` em `VeiculoModel` (ORM)."""
        return VeiculoModel(
            id=veiculo.id,
            marca=veiculo.marca,
            modelo=veiculo.modelo,
            ano=veiculo.ano.valor,
            cor=veiculo.cor,
            preco=veiculo.preco.valor,
            status=veiculo.status.value,
            created_at=veiculo.created_at,
            updated_at=veiculo.updated_at,
        )

    @staticmethod
    def _model_to_entity(model: VeiculoModel) -> Veiculo:
        """Converte `VeiculoModel` (ORM) na entidade de dominio `Veiculo`."""
        return Veiculo(
            id=model.id,
            marca=model.marca,
            modelo=model.modelo,
            ano=Ano(valor=model.ano),
            cor=model.cor,
            preco=Preco(valor=model.preco),
            status=StatusVeiculo(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
