"""Dependencias FastAPI do servico de auth (wiring do provedor de identidade).

Expoe o provider concreto (`IdentityProvider` -> Cognito) via `Depends`,
facil de sobrescrever nos testes com `app.dependency_overrides`.
"""

from typing import Annotated

from fastapi import Depends

from src.application.ports.identity_provider import IdentityProvider
from src.environment import Settings, get_settings
from src.infrastructure.aws.cognito_client import get_cognito_client
from src.interface.gateways.cognito_identity_provider_gateway import CognitoIdentityProvider

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_identity_provider(settings: SettingsDep) -> IdentityProvider:
    """Fornece o provedor de identidade (Cognito).

    Args:
        settings: Configuracoes resolvidas da aplicacao.

    Returns:
        Adapter concreto do `IdentityProvider` sobre o Cognito.
    """
    client = get_cognito_client(settings.auth.aws_region, settings.auth.aws_endpoint_url)
    return CognitoIdentityProvider(
        client,
        settings.auth.cognito_client_id,
        settings.auth.cognito_user_pool_id,
    )


IdentityDep = Annotated[IdentityProvider, Depends(get_identity_provider)]
