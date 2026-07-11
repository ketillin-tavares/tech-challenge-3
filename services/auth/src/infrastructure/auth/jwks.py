"""Cliente JWKS do Cognito (cacheado por processo)."""

from functools import lru_cache

from jwt import PyJWKClient


@lru_cache
def get_jwks_client(jwks_url: str) -> PyJWKClient:
    """Retorna um `PyJWKClient` unico por URL de JWKS.

    O `PyJWKClient` ja cacheia as chaves internamente; o `lru_cache` garante
    uma unica instancia por processo (evita refetch e novas conexoes).

    Args:
        jwks_url: URL do documento JWKS do User Pool.

    Returns:
        Instancia cacheada de `PyJWKClient`.
    """
    return PyJWKClient(jwks_url)
