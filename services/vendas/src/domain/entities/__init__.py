"""Entidades do dominio transacional: Veiculo e Venda.

As entidades concentram as regras invariantes da empresa. As transicoes de
estado sao expressas como metodos que falham com excecoes de dominio quando
violadas (nunca com codigos HTTP).
"""

from src.domain.entities.veiculo import Veiculo
from src.domain.entities.venda import Venda

__all__ = ["Veiculo", "Venda"]
