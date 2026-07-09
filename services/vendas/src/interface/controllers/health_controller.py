"""Controller de health check (liveness probe)."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health", summary="Liveness probe")
async def health() -> dict[str, str]:
    """Indica que o processo da API esta vivo.

    Returns:
        Dicionario simples de status, sem dependencias externas.
    """
    return {"status": "ok"}
