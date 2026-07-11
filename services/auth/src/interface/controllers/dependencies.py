"""Dependencias FastAPI do servico de auth (wiring de identidade e ACL).

Expoe o provider concreto (`IdentityProvider` -> Cognito) via `Depends` e as
dependencias de autenticacao/autorizacao dos endpoints de perfil: o token
Bearer e validado localmente (`TokenVerifier` via JWKS, mesmo padrao do
servico de vendas) e convertido em `ClienteAutenticado`. Tudo facil de
sobrescrever nos testes com `app.dependency_overrides`.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.ports.identity_provider import IdentityProvider
from src.application.ports.token_verifier import TokenVerifier
from src.domain.exceptions import TokenInvalidoError
from src.domain.value_objects import ClienteAutenticado
from src.environment import Settings, get_settings
from src.infrastructure.auth import JwtTokenVerifier, get_jwks_client
from src.infrastructure.aws.cognito_client import get_cognito_client
from src.interface.gateways.cognito_identity_provider_gateway import CognitoIdentityProvider

GRUPO_ADMIN = "admin"

_bearer = HTTPBearer(auto_error=False)

SettingsDep = Annotated[Settings, Depends(get_settings)]
CredenciaisDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


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


def get_token_verifier(settings: SettingsDep) -> TokenVerifier:
    """Fornece o verificador de JWT configurado para o User Pool.

    Args:
        settings: Configuracoes resolvidas da aplicacao.

    Returns:
        Verificador concreto de access tokens do Cognito.
    """
    jwks_client = get_jwks_client(settings.auth.jwks_url)
    return JwtTokenVerifier(
        jwks_client,
        issuer=settings.auth.cognito_issuer,
        client_id=settings.auth.cognito_client_id,
    )


VerifierDep = Annotated[TokenVerifier, Depends(get_token_verifier)]


async def token_bearer(credenciais: CredenciaisDep) -> str:
    """Extrai o access token bruto do cabecalho Authorization.

    Usado pelo endpoint de perfil proprio, que repassa o token ao provedor
    (`GetUser` e autorizado pelo proprio token do cliente).

    Args:
        credenciais: Credenciais Bearer extraidas do cabecalho Authorization.

    Returns:
        Access token sem o prefixo "Bearer".

    Raises:
        TokenInvalidoError: Se nao houver token (traduzido para 401).
    """
    if credenciais is None:
        raise TokenInvalidoError
    return credenciais.credentials


TokenDep = Annotated[str, Depends(token_bearer)]


async def cliente_autenticado(
    credenciais: CredenciaisDep,
    verifier: VerifierDep,
) -> ClienteAutenticado:
    """Valida o token Bearer e retorna a identidade autenticada.

    Args:
        credenciais: Credenciais Bearer extraidas do cabecalho Authorization.
        verifier: Verificador de token injetado.

    Returns:
        Identidade do cliente autenticado.

    Raises:
        TokenInvalidoError: Se nao houver token (traduzido para 401).
    """
    if credenciais is None:
        raise TokenInvalidoError
    return verifier.verificar(credenciais.credentials)


ClienteDep = Annotated[ClienteAutenticado, Depends(cliente_autenticado)]


async def requer_admin(cliente: ClienteDep) -> ClienteAutenticado:
    """Exige que o cliente autenticado pertenca ao grupo de administradores.

    Args:
        cliente: Identidade autenticada (resolvida por `cliente_autenticado`).

    Returns:
        A propria identidade, se autorizada.

    Raises:
        HTTPException: 403 se o cliente nao pertencer ao grupo admin.
    """
    if not cliente.tem_grupo(GRUPO_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return cliente


AdminDep = Annotated[ClienteAutenticado, Depends(requer_admin)]
