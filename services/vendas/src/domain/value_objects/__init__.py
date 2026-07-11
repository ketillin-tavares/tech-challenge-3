"""Value Objects do dominio de vendas (imutaveis e auto-validados).

Usam `pydantic` (unica dependencia externa permitida no dominio). Construir com
valor invalido levanta `pydantic.ValidationError`, traduzida para 422 na borda.
"""

from src.domain.value_objects.ano import ANO_MINIMO, Ano
from src.domain.value_objects.identidade import ClienteAutenticado
from src.domain.value_objects.preco import Preco
from src.domain.value_objects.status_veiculo import StatusVeiculo
from src.domain.value_objects.status_venda import StatusVenda

__all__ = [
    "ANO_MINIMO",
    "Ano",
    "ClienteAutenticado",
    "Preco",
    "StatusVeiculo",
    "StatusVenda",
]
