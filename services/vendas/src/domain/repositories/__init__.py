"""Ports (interfaces abstratas) do dominio transacional.

Definem os contratos que a camada de Interface Adapters implementa
(repositorios concretos, unidade de trabalho). As camadas internas dependem
destas abstracoes, nunca das implementacoes (DIP).
"""

from src.domain.repositories.unit_of_work import UnitOfWork
from src.domain.repositories.veiculo_repository import VeiculoRepository
from src.domain.repositories.venda_repository import VendaRepository

__all__ = ["UnitOfWork", "VeiculoRepository", "VendaRepository"]
