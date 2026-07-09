"""Presenter de erros: envelope padronizado de resposta de erro da API.

O dominio nao conhece HTTP; a traducao excecao -> resposta acontece nos
handlers registrados no `main.py`. Aqui mora apenas a *estrutura* da resposta
(usada tambem na documentacao OpenAPI via ``responses=``).
"""

from typing import Any

from pydantic import BaseModel, Field


class ErroResponse(BaseModel):
    """Envelope padronizado de erro (RFC7807-like)."""

    status: int = Field(description="Codigo HTTP do erro.")
    code: str = Field(description="Codigo simbolico do erro (ex.: VEICULO_NAO_ENCONTRADO).")
    detail: Any = Field(description="Mensagem legivel ou lista de campos invalidos.")
