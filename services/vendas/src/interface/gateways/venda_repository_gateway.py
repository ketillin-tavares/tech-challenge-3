"""Gateway de persistencia de vendas (SQLAlchemy)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Venda
from src.domain.exceptions import VeiculoIndisponivelError
from src.domain.repositories.venda_repository import VendaRepository
from src.domain.value_objects import Preco
from src.infrastructure.logging import get_logger
from src.infrastructure.models import VendaModel

logger = get_logger()


class VendaRepositoryGateway(VendaRepository):
    """Adapter que implementa `VendaRepository` usando SQLAlchemy."""

    def __init__(self, session: AsyncSession) -> None:
        """Recebe a sessao async do banco.

        Args:
            session: Sessao SQLAlchemy ligada a transacao em curso.
        """
        self._session = session

    async def adicionar(self, venda: Venda) -> None:
        """Persiste uma nova venda.

        Faz `flush` para forcar o INSERT agora e capturar a violacao da
        constraint UNIQUE (`veiculo_id`), traduzindo-a para o erro de dominio.

        Args:
            venda: Venda a persistir.

        Raises:
            VeiculoIndisponivelError: Se o veiculo ja possui venda (dupla compra).
        """
        self._session.add(self._entity_to_model(venda))
        try:
            await self._session.flush()
        except IntegrityError as exc:
            logger.bind(veiculo_id=str(venda.veiculo_id)).info("venda_duplicada")
            raise VeiculoIndisponivelError(venda.veiculo_id) from exc

    async def obter_por_veiculo(self, veiculo_id: UUID) -> Venda | None:
        """Retorna a venda associada a um veiculo, ou None."""
        stmt = select(VendaModel).where(VendaModel.veiculo_id == veiculo_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model is not None else None

    @staticmethod
    def _entity_to_model(venda: Venda) -> VendaModel:
        """Converte a entidade `Venda` em `VendaModel` (ORM)."""
        return VendaModel(
            id=venda.id,
            veiculo_id=venda.veiculo_id,
            cliente_id=venda.cliente_id,
            preco_venda=venda.preco_venda.valor,
            data_venda=venda.data_venda,
            created_at=venda.created_at,
        )

    @staticmethod
    def _model_to_entity(model: VendaModel) -> Venda:
        """Converte `VendaModel` (ORM) na entidade de dominio `Venda`."""
        return Venda(
            id=model.id,
            veiculo_id=model.veiculo_id,
            cliente_id=model.cliente_id,
            preco_venda=Preco(valor=model.preco_venda),
            data_venda=model.data_venda,
            created_at=model.created_at,
        )
