"""Barrel dos modelos ORM (necessario para o Alembic autodetectar o schema)."""

from src.infrastructure.models.base import Base
from src.infrastructure.models.veiculo_model import VeiculoModel
from src.infrastructure.models.venda_model import VendaModel

__all__ = ["Base", "VeiculoModel", "VendaModel"]
