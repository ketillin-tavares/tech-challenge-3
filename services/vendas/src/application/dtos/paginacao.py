"""DTO de paginacao compartilhado pelas listagens."""

from pydantic import BaseModel, Field


class PaginacaoQuery(BaseModel):
    """Parametros de paginacao para listagens (validados na borda)."""

    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
