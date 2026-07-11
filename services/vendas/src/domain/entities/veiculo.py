"""Entidade Veiculo."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.exceptions import VeiculoIndisponivelError, VeiculoVendidoNaoEditavelError
from src.domain.value_objects import Ano, Preco, StatusVeiculo


class Veiculo(BaseModel):
    """Item a venda com ciclo de vida DISPONIVEL -> RESERVADO -> VENDIDO.

    O cancelamento ou a expiracao da reserva devolve o veiculo a DISPONIVEL.

    Atributos:
        id: Identificador unico do veiculo.
        marca: Fabricante.
        modelo: Modelo.
        ano: Ano de fabricacao (VO validado).
        cor: Cor.
        preco: Preco corrente (VO validado).
        status: Estado atual; nasce DISPONIVEL.
        created_at: Momento de criacao.
        updated_at: Momento da ultima alteracao.
    """

    model_config = ConfigDict(validate_assignment=True)

    id: UUID
    marca: str = Field(min_length=1)
    modelo: str = Field(min_length=1)
    ano: Ano
    cor: str = Field(min_length=1)
    preco: Preco
    status: StatusVeiculo = StatusVeiculo.DISPONIVEL
    created_at: datetime
    updated_at: datetime

    def reservar(self) -> None:
        """Transita o veiculo de DISPONIVEL para RESERVADO (compra iniciada).

        Raises:
            VeiculoIndisponivelError: Se o veiculo nao estiver DISPONIVEL.
        """
        if self.status is not StatusVeiculo.DISPONIVEL:
            raise VeiculoIndisponivelError(self.id)
        self.status = StatusVeiculo.RESERVADO
        self.updated_at = datetime.now(UTC)

    def liberar_reserva(self) -> None:
        """Transita o veiculo de RESERVADO de volta para DISPONIVEL.

        Ocorre no cancelamento da compra ou na expiracao da reserva.

        Raises:
            VeiculoIndisponivelError: Se o veiculo nao estiver RESERVADO.
        """
        if self.status is not StatusVeiculo.RESERVADO:
            raise VeiculoIndisponivelError(self.id)
        self.status = StatusVeiculo.DISPONIVEL
        self.updated_at = datetime.now(UTC)

    def marcar_como_vendido(self) -> None:
        """Transita o veiculo de RESERVADO para VENDIDO (compra efetivada).

        A transicao e unica e irreversivel; exige reserva previa (`reservar`).

        Raises:
            VeiculoIndisponivelError: Se o veiculo nao estiver RESERVADO.
        """
        if self.status is not StatusVeiculo.RESERVADO:
            raise VeiculoIndisponivelError(self.id)
        self.status = StatusVeiculo.VENDIDO
        self.updated_at = datetime.now(UTC)

    def atualizar_dados(
        self,
        *,
        marca: str,
        modelo: str,
        ano: Ano,
        cor: str,
        preco: Preco,
    ) -> None:
        """Substitui os dados cadastrais do veiculo (edicao total).

        Args:
            marca: Nova marca.
            modelo: Novo modelo.
            ano: Novo ano (VO).
            cor: Nova cor.
            preco: Novo preco (VO).

        Raises:
            VeiculoVendidoNaoEditavelError: Se o veiculo ja estiver VENDIDO.
        """
        if self.status is StatusVeiculo.VENDIDO:
            raise VeiculoVendidoNaoEditavelError(self.id)
        self.marca = marca
        self.modelo = modelo
        self.ano = ano
        self.cor = cor
        self.preco = preco
        self.updated_at = datetime.now(UTC)
