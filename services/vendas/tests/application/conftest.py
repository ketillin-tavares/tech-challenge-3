"""Dubles de teste (fakes) dos ports e construtores de entidades.

Os fakes implementam os ports abstratos (write-side e read-side) -> testamos
as interfaces injetadas, nunca adapters concretos (sem I/O real). Cada fake
registra suas chamadas para permitir asserts de interacao.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import TracebackType
from uuid import UUID, uuid4

from src.application.dtos import VeiculoDTO, VeiculoVendidoDTO
from src.application.ports import VeiculoQueryService
from src.domain.entities import Veiculo, Venda
from src.domain.repositories import UnitOfWork, VeiculoRepository, VendaRepository
from src.domain.value_objects import Ano, Preco, StatusVeiculo, StatusVenda


def construir_veiculo(
    *,
    status: StatusVeiculo = StatusVeiculo.DISPONIVEL,
    preco: str = "85000.00",
    veiculo_id: UUID | None = None,
) -> Veiculo:
    """Cria um veiculo valido para os testes."""
    agora = datetime.now(UTC)
    return Veiculo(
        id=veiculo_id or uuid4(),
        marca="Toyota",
        modelo="Corolla",
        ano=Ano(valor=2020),
        cor="Prata",
        preco=Preco(valor=Decimal(preco)),
        status=status,
        created_at=agora,
        updated_at=agora,
    )


def construir_venda(
    *,
    veiculo_id: UUID | None = None,
    cliente_id: str = "sub-cliente-123",
    preco_venda: str = "85000.00",
    expira_em: datetime | None = None,
) -> Venda:
    """Cria uma venda valida para os testes."""
    agora = datetime.now(UTC)
    return Venda(
        id=uuid4(),
        veiculo_id=veiculo_id or uuid4(),
        cliente_id=cliente_id,
        preco_venda=Preco(valor=Decimal(preco_venda)),
        status=StatusVenda.PENDENTE,
        expira_em=expira_em or (agora + timedelta(hours=1)),
        created_at=agora,
        updated_at=agora,
    )


class FakeVeiculoRepository(VeiculoRepository):
    """Repositorio de veiculos em memoria que registra interacoes."""

    def __init__(self) -> None:
        self._dados: dict[UUID, Veiculo] = {}
        self.adicionados: list[Veiculo] = []
        self.atualizados: list[Veiculo] = []

    def semear(self, veiculo: Veiculo) -> None:
        """Pre-popula o repositorio sem registrar como interacao de teste."""
        self._dados[veiculo.id] = veiculo

    async def adicionar(self, veiculo: Veiculo) -> None:
        self.adicionados.append(veiculo)
        self._dados[veiculo.id] = veiculo

    async def obter_por_id(self, veiculo_id: UUID) -> Veiculo | None:
        return self._dados.get(veiculo_id)

    async def listar_por_status(
        self,
        status: StatusVeiculo,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Veiculo]:
        itens = sorted(
            (v for v in self._dados.values() if v.status is status),
            key=lambda v: v.preco.valor,
        )
        return itens[offset : offset + limit]

    async def atualizar(self, veiculo: Veiculo) -> None:
        self.atualizados.append(veiculo)
        self._dados[veiculo.id] = veiculo


class FakeVendaRepository(VendaRepository):
    """Repositorio de vendas em memoria; pode simular violacao de unicidade."""

    def __init__(self, erro_ao_adicionar: Exception | None = None) -> None:
        self._dados: dict[UUID, Venda] = {}
        self._dados_por_id: dict[UUID, Venda] = {}
        self.adicionadas: list[Venda] = []
        self.atualizadas: list[Venda] = []
        self._erro_ao_adicionar = erro_ao_adicionar

    def semear(self, venda: Venda) -> None:
        """Pre-popula o repositorio sem registrar como interacao de teste."""
        self._dados[venda.veiculo_id] = venda
        self._dados_por_id[venda.id] = venda

    async def adicionar(self, venda: Venda) -> None:
        if self._erro_ao_adicionar is not None:
            raise self._erro_ao_adicionar
        self.adicionadas.append(venda)
        self._dados[venda.veiculo_id] = venda
        self._dados_por_id[venda.id] = venda

    async def obter_por_veiculo(self, veiculo_id: UUID) -> Venda | None:
        return self._dados.get(veiculo_id)

    async def obter_por_id(self, venda_id: UUID) -> Venda | None:
        """Obtém uma venda pelo seu id."""
        return self._dados_por_id.get(venda_id)

    async def obter_pendente_por_cliente(self, cliente_id: str) -> Venda | None:
        """Obtém a venda PENDENTE do cliente (no máximo uma)."""
        from src.domain.value_objects import StatusVenda

        for venda in self._dados_por_id.values():
            if venda.cliente_id == cliente_id and venda.status is StatusVenda.PENDENTE:
                return venda
        return None

    async def listar_pendentes_expiradas(self, agora: datetime, limite: int) -> list[Venda]:
        """Lista vendas PENDENTE com reserva expirada."""
        vendas_expiradas = [v for v in self._dados_por_id.values() if v.esta_expirada(agora)]
        return vendas_expiradas[:limite]

    async def atualizar(self, venda: Venda) -> None:
        """Atualiza uma venda existente."""
        self.atualizadas.append(venda)
        self._dados[venda.veiculo_id] = venda
        self._dados_por_id[venda.id] = venda


class FakeUnitOfWork(UnitOfWork):
    """Unidade de trabalho fake que conta commits/rollbacks."""

    def __init__(self, veiculos: VeiculoRepository, vendas: VendaRepository) -> None:
        self.veiculos = veiculos
        self.vendas = vendas
        self.commits = 0
        self.rollbacks = 0

    async def __aenter__(self) -> "FakeUnitOfWork":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc_type is not None:
            await self.rollback()

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


class FakeVeiculoQueryService(VeiculoQueryService):
    """Servico de consultas fake que devolve DTOs pre-definidos."""

    def __init__(
        self,
        disponiveis: list[VeiculoDTO] | None = None,
        vendidos: list[VeiculoVendidoDTO] | None = None,
    ) -> None:
        self._disponiveis = disponiveis or []
        self._vendidos = vendidos or []
        self.chamadas_disponiveis: list[tuple[int, int]] = []
        self.chamadas_vendidos: list[tuple[int, int]] = []

    async def listar_disponiveis(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[VeiculoDTO]:
        self.chamadas_disponiveis.append((limit, offset))
        return self._disponiveis

    async def listar_vendidos(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[VeiculoVendidoDTO]:
        self.chamadas_vendidos.append((limit, offset))
        return self._vendidos
