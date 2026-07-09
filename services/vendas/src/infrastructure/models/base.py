"""Classe base declarativa dos modelos ORM."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Classe base para todos os modelos SQLAlchemy do servico."""
