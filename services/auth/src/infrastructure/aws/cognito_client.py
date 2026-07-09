"""Fabrica do cliente boto3 do Cognito Identity Provider (cacheado)."""

from functools import lru_cache
from typing import Any

import boto3


@lru_cache
def get_cognito_client(region: str, endpoint_url: str = "") -> Any:
    """Retorna um cliente boto3 `cognito-idp` unico por (regiao, endpoint).

    O tipo de retorno e `Any` porque o boto3 nao expoe stubs de tipo neste
    projeto; o adapter `CognitoIdentityProvider` encapsula seu uso.

    Args:
        region: Regiao AWS do User Pool.
        endpoint_url: Endpoint customizado (ex.: LocalStack). Vazio => AWS real.

    Returns:
        Cliente boto3 `cognito-idp`.
    """
    return boto3.client("cognito-idp", region_name=region, endpoint_url=endpoint_url or None)
