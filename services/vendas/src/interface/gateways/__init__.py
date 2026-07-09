"""Gateways (Adapters) -- implementacoes concretas das Ports de vendas."""

from src.interface.gateways.unit_of_work_gateway import UnitOfWorkGateway
from src.interface.gateways.veiculo_query_service_gateway import VeiculoQueryServiceGateway
from src.interface.gateways.veiculo_repository_gateway import VeiculoRepositoryGateway
from src.interface.gateways.venda_repository_gateway import VendaRepositoryGateway

__all__ = [
    "UnitOfWorkGateway",
    "VeiculoQueryServiceGateway",
    "VeiculoRepositoryGateway",
    "VendaRepositoryGateway",
]
