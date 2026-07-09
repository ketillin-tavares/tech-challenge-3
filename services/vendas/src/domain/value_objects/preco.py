"""Value Object Preco."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class Preco(BaseModel):
    """Valor monetario positivo com ate 2 casas decimais.

    Usa `Decimal` para precisao monetaria (nunca float).

    Atributos:
        valor: Montante estritamente positivo, com no maximo 2 casas decimais.
    """

    model_config = ConfigDict(frozen=True)

    valor: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
