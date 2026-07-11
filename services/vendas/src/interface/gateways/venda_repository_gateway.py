"""Gateway de persistencia de vendas (SQLAlchemy)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import Venda
from src.domain.exceptions import ReservaAtivaExistenteError, VeiculoIndisponivelError
from src.domain.repositories.venda_repository import VendaRepository
from src.domain.value_objects import Preco, StatusVenda
from src.infrastructure.logging import get_logger
from src.infrastructure.models import VendaModel

logger = get_logger()

_CONSTRAINT_CLIENTE_PENDENTE = "uq_vendas_cliente_pendente"


class VendaRepositoryGateway(VendaRepository):
    """Adapter que implementa `VendaRepository` usando SQLAlchemy.

    As leituras dos fluxos de escrita usam lock pessimista (`FOR UPDATE`),
    detalhe deste adapter: elimina corridas entre efetivar, cancelar e a
    varredura de expiracao sem vazar locking para as camadas internas.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Recebe a sessao async do banco.

        Args:
            session: Sessao SQLAlchemy ligada a transacao em curso.
        """
        self._session = session

    async def adicionar(self, venda: Venda) -> None:
        """Persiste uma nova venda.

        Faz `flush` para forcar o INSERT agora e capturar a violacao dos
        indices unicos parciais, traduzindo-a para o erro de dominio pelo NOME
        da constraint violada (sem propagar o detail do driver).

        Args:
            venda: Venda a persistir.

        Raises:
            ReservaAtivaExistenteError: Se o cliente ja tem venda PENDENTE.
            VeiculoIndisponivelError: Se o veiculo ja possui venda ativa.
        """
        self._session.add(self._entity_to_model(venda))
        try:
            await self._session.flush()
        except IntegrityError as exc:
            if _CONSTRAINT_CLIENTE_PENDENTE in str(exc.orig):
                logger.bind(cliente_id=venda.cliente_id).info("reserva_ativa_duplicada")
                raise ReservaAtivaExistenteError from exc
            logger.bind(veiculo_id=str(venda.veiculo_id)).info("venda_duplicada")
            raise VeiculoIndisponivelError(venda.veiculo_id) from exc

    async def obter_por_id(self, venda_id: UUID) -> Venda | None:
        """Retorna a venda pelo id, ou None (lock pessimista na linha)."""
        stmt = select(VendaModel).where(VendaModel.id == venda_id).with_for_update()
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model is not None else None

    async def obter_por_veiculo(self, veiculo_id: UUID) -> Venda | None:
        """Retorna a venda mais recente associada a um veiculo, ou None."""
        stmt = (
            select(VendaModel)
            .where(VendaModel.veiculo_id == veiculo_id)
            .order_by(VendaModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model is not None else None

    async def obter_pendente_por_cliente(self, cliente_id: str) -> Venda | None:
        """Retorna a venda PENDENTE do cliente, ou None se nao houver."""
        stmt = select(VendaModel).where(
            VendaModel.cliente_id == cliente_id,
            VendaModel.status == StatusVenda.PENDENTE.value,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model is not None else None

    async def listar_pendentes_expiradas(self, agora: datetime, limite: int) -> list[Venda]:
        """Lista vendas PENDENTE vencidas, pulando linhas ja bloqueadas.

        `FOR UPDATE SKIP LOCKED` permite que a varredura conviva com as
        transicoes disparadas por usuarios (mesma ordem de lock venda ->
        veiculo) sem deadlock nem processamento duplicado entre execucoes
        concorrentes.
        """
        stmt = (
            select(VendaModel)
            .where(
                VendaModel.status == StatusVenda.PENDENTE.value,
                VendaModel.expira_em <= agora,
            )
            .limit(limite)
            .with_for_update(skip_locked=True)
        )
        result = await self._session.execute(stmt)
        return [self._model_to_entity(model) for model in result.scalars().all()]

    async def atualizar(self, venda: Venda) -> None:
        """Aplica as alteracoes de uma venda existente (read-modify-write)."""
        model = await self._session.get(VendaModel, venda.id)
        if model is None:
            return
        model.status = venda.status.value
        model.expira_em = venda.expira_em
        model.data_venda = venda.data_venda
        model.updated_at = venda.updated_at

    @staticmethod
    def _entity_to_model(venda: Venda) -> VendaModel:
        """Converte a entidade `Venda` em `VendaModel` (ORM)."""
        return VendaModel(
            id=venda.id,
            veiculo_id=venda.veiculo_id,
            cliente_id=venda.cliente_id,
            preco_venda=venda.preco_venda.valor,
            status=venda.status.value,
            expira_em=venda.expira_em,
            data_venda=venda.data_venda,
            created_at=venda.created_at,
            updated_at=venda.updated_at,
        )

    @staticmethod
    def _model_to_entity(model: VendaModel) -> Venda:
        """Converte `VendaModel` (ORM) na entidade de dominio `Venda`."""
        return Venda(
            id=model.id,
            veiculo_id=model.veiculo_id,
            cliente_id=model.cliente_id,
            preco_venda=Preco(valor=model.preco_venda),
            status=StatusVenda(model.status),
            expira_em=model.expira_em,
            data_venda=model.data_venda,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
