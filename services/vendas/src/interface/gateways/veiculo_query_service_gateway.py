"""Gateway do read-model de veiculos (SQLAlchemy)."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.dtos.veiculo import VeiculoDTO, VeiculoVendidoDTO
from src.application.ports.veiculo_query_service import VeiculoQueryService
from src.domain.value_objects import StatusVeiculo
from src.infrastructure.models import VeiculoModel, VendaModel


class VeiculoQueryServiceGateway(VeiculoQueryService):
    """Read-model de veiculos: monta DTOs direto das colunas (sem entidade)."""

    def __init__(self, session: AsyncSession) -> None:
        """Recebe a sessao async do banco.

        Args:
            session: Sessao SQLAlchemy para as consultas de leitura.
        """
        self._session = session

    async def listar_disponiveis(self, *, limit: int = 50, offset: int = 0) -> list[VeiculoDTO]:
        """Lista veiculos DISPONIVEIS, por preco ascendente (paginado)."""
        stmt = (
            select(VeiculoModel)
            .where(VeiculoModel.status == StatusVeiculo.DISPONIVEL.value)
            .order_by(VeiculoModel.preco.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_veiculo_dto(model) for model in result.scalars().all()]

    async def listar_vendidos(self, *, limit: int = 50, offset: int = 0) -> list[VeiculoVendidoDTO]:
        """Lista veiculos VENDIDOS com os dados da venda (JOIN unico, sem N+1)."""
        stmt = (
            select(VeiculoModel, VendaModel)
            .join(VendaModel, VendaModel.veiculo_id == VeiculoModel.id)
            .where(VeiculoModel.status == StatusVeiculo.VENDIDO.value)
            .order_by(VeiculoModel.preco.asc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return [self._to_vendido_dto(veiculo, venda) for veiculo, venda in result.all()]

    @staticmethod
    def _to_veiculo_dto(model: VeiculoModel) -> VeiculoDTO:
        """Monta um `VeiculoDTO` a partir da linha de `veiculos`."""
        return VeiculoDTO(
            id=model.id,
            marca=model.marca,
            modelo=model.modelo,
            ano=model.ano,
            cor=model.cor,
            preco=model.preco,
            status=StatusVeiculo(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_vendido_dto(veiculo: VeiculoModel, venda: VendaModel) -> VeiculoVendidoDTO:
        """Monta um `VeiculoVendidoDTO` a partir do JOIN veiculo+venda."""
        return VeiculoVendidoDTO(
            id=veiculo.id,
            marca=veiculo.marca,
            modelo=veiculo.modelo,
            ano=veiculo.ano,
            cor=veiculo.cor,
            preco=veiculo.preco,
            status=StatusVeiculo(veiculo.status),
            created_at=veiculo.created_at,
            updated_at=veiculo.updated_at,
            preco_venda=venda.preco_venda,
            data_venda=venda.data_venda,
        )
