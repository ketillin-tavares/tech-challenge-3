"""Dependencias de autenticacao/autorizacao da API (ACL).

Convertem o token Bearer em uma identidade de dominio (`ClienteAutenticado`)
e aplicam a politica de autorizacao por grupo. A validacao criptografica fica
no `TokenVerifier` (infra, via JWKS do Cognito); aqui so se orquestra a
politica. Nao ha chamada ao servico de auth em runtime.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.application.ports.token_verifier import TokenVerifier
from src.domain.exceptions import TokenInvalidoError
from src.domain.value_objects import ClienteAutenticado
from src.environment import Settings, get_settings
from src.infrastructure.auth.jwks import get_jwks_client
from src.infrastructure.auth.jwt_token_verifier import JwtTokenVerifier

GRUPO_ADMIN = "admin"

_bearer = HTTPBearer(auto_error=False)

SettingsDep = Annotated[Settings, Depends(get_settings)]
CredenciaisDep = Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]


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
