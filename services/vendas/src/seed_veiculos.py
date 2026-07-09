"""Massa de dados de veiculos para ambientes locais (idempotente).

Este script popula a tabela `veiculos` com um catalogo fixo de carros para
facilitar testes manuais da API em desenvolvimento. Roda como um servico
one-shot no docker-compose, apos as migrations e antes da aplicacao subir.

Idempotencia: cada veiculo recebe um UUID deterministico (uuid5) derivado dos
seus dados cadastrais. Antes de inserir, o script verifica se o id ja existe,
de modo que reexecucoes nao duplicam registros nem falham.

Reutiliza a entidade de dominio `Veiculo` e o gateway concreto de persistencia,
sem vazar detalhes de ORM para fora deste script de infraestrutura.
"""

import asyncio
from datetime import UTC, datetime
from decimal import Decimal
from uuid import NAMESPACE_URL, UUID, uuid5

from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

from src.domain.entities import Veiculo
from src.domain.value_objects import Ano, Preco
from src.infrastructure.database.session import async_engine, async_session_factory
from src.interface.gateways import VeiculoRepositoryGateway

# Namespace fixo para derivar UUIDs deterministicos da massa de dados. Manter
# estavel garante que os mesmos carros gerem sempre os mesmos ids (idempotencia).
_SEED_NAMESPACE: UUID = uuid5(NAMESPACE_URL, "tech-challenge-3/seed/veiculos")


class VeiculoSeedSpec(BaseModel):
    """Especificacao imutavel de um veiculo da massa de dados.

    Atributos:
        marca: Fabricante.
        modelo: Modelo.
        ano: Ano de fabricacao.
        cor: Cor.
        preco: Preco de tabela.
    """

    model_config = ConfigDict(frozen=True)

    marca: str = Field(min_length=1)
    modelo: str = Field(min_length=1)
    ano: int
    cor: str = Field(min_length=1)
    preco: Decimal = Field(gt=0)


# Catalogo fixo de veiculos DISPONIVEIS para testes locais.
MASSA_VEICULOS: tuple[VeiculoSeedSpec, ...] = (
    VeiculoSeedSpec(
        marca="Volkswagen", modelo="Gol", ano=2018, cor="Branco", preco=Decimal("42900.00")
    ),
    VeiculoSeedSpec(
        marca="Volkswagen", modelo="Polo", ano=2022, cor="Prata", preco=Decimal("89900.00")
    ),
    VeiculoSeedSpec(
        marca="Fiat", modelo="Argo", ano=2021, cor="Vermelho", preco=Decimal("74500.00")
    ),
    VeiculoSeedSpec(marca="Fiat", modelo="Toro", ano=2023, cor="Cinza", preco=Decimal("139900.00")),
    VeiculoSeedSpec(
        marca="Chevrolet", modelo="Onix", ano=2020, cor="Preto", preco=Decimal("68900.00")
    ),
    VeiculoSeedSpec(
        marca="Chevrolet", modelo="Tracker", ano=2023, cor="Branco", preco=Decimal("129900.00")
    ),
    VeiculoSeedSpec(marca="Ford", modelo="Ka", ano=2019, cor="Azul", preco=Decimal("51900.00")),
    VeiculoSeedSpec(
        marca="Toyota", modelo="Corolla", ano=2022, cor="Prata", preco=Decimal("164900.00")
    ),
    VeiculoSeedSpec(
        marca="Toyota", modelo="Hilux", ano=2024, cor="Branco", preco=Decimal("289900.00")
    ),
    VeiculoSeedSpec(
        marca="Honda", modelo="Civic", ano=2021, cor="Cinza", preco=Decimal("158900.00")
    ),
    VeiculoSeedSpec(
        marca="Honda", modelo="HR-V", ano=2023, cor="Preto", preco=Decimal("172900.00")
    ),
    VeiculoSeedSpec(
        marca="Hyundai", modelo="HB20", ano=2020, cor="Vermelho", preco=Decimal("64900.00")
    ),
    VeiculoSeedSpec(
        marca="Hyundai", modelo="Creta", ano=2023, cor="Azul", preco=Decimal("134900.00")
    ),
    VeiculoSeedSpec(
        marca="Renault", modelo="Kwid", ano=2022, cor="Laranja", preco=Decimal("58900.00")
    ),
    VeiculoSeedSpec(
        marca="Jeep", modelo="Renegade", ano=2021, cor="Verde", preco=Decimal("119900.00")
    ),
)


def _id_deterministico(spec: VeiculoSeedSpec) -> UUID:
    """Deriva um UUID estavel a partir dos dados cadastrais do veiculo.

    Args:
        spec: Especificacao do veiculo.

    Returns:
        UUID deterministico (uuid5) unico para a combinacao marca/modelo/ano/cor.
    """
    chave = f"{spec.marca}|{spec.modelo}|{spec.ano}|{spec.cor}"
    return uuid5(_SEED_NAMESPACE, chave)


def _construir_massa() -> list[Veiculo]:
    """Constroi as entidades de dominio `Veiculo` da massa de dados.

    Os Value Objects sao validados aqui e cada veiculo recebe um id
    deterministico, garantindo idempotencia entre execucoes.

    Returns:
        Lista de veiculos DISPONIVEIS prontos para persistir.
    """
    agora = datetime.now(UTC)
    return [
        Veiculo(
            id=_id_deterministico(spec),
            marca=spec.marca,
            modelo=spec.modelo,
            ano=Ano(valor=spec.ano),
            cor=spec.cor,
            preco=Preco(valor=spec.preco),
            created_at=agora,
            updated_at=agora,
        )
        for spec in MASSA_VEICULOS
    ]


async def main() -> None:
    """Aplica a massa de veiculos no banco configurado (idempotente).

    Ponto de entrada do servico one-shot do docker-compose. Abre uma sessao,
    insere apenas os veiculos ausentes, confirma a transacao e libera o engine.
    """
    inseridos = 0
    try:
        async with async_session_factory() as session:
            repositorio = VeiculoRepositoryGateway(session)
            for veiculo in _construir_massa():
                if await repositorio.obter_por_id(veiculo.id) is not None:
                    continue
                await repositorio.adicionar(veiculo)
                inseridos += 1
            await session.commit()
        logger.info(
            "Massa de veiculos aplicada: {} inseridos, {} ja existentes.",
            inseridos,
            len(MASSA_VEICULOS) - inseridos,
        )
    finally:
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
