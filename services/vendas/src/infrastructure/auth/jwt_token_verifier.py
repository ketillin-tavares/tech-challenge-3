"""Adapter de verificacao de JWT do Cognito via JWKS (pyjwt)."""

import jwt
from jwt import PyJWKClient

from src.application.ports.token_verifier import TokenVerifier
from src.domain.exceptions import TokenInvalidoError
from src.domain.value_objects import ClienteAutenticado

_ALGORITMOS = ["RS256"]
_TOKEN_USE_ESPERADO = "access"


class JwtTokenVerifier(TokenVerifier):
    """Verifica ACCESS tokens do Cognito (assinatura, iss, exp, client_id).

    Segue a especificacao OAuth2/OIDC: o access token e o credencial correto
    para autorizar chamadas de API. O access token do Cognito nao possui claim
    `aud` -- ele amarra o token ao App Client pelo claim `client_id`, que e o
    que validamos aqui (evita aceitar tokens de outro App Client do mesmo pool).
    """

    def __init__(self, jwks_client: PyJWKClient, issuer: str, client_id: str) -> None:
        """Recebe o cliente JWKS e os valores esperados de iss/client_id.

        Args:
            jwks_client: Cliente JWKS (cacheado) do User Pool.
            issuer: Emissor esperado (claim `iss`).
            client_id: App Client esperado (claim `client_id` do access token).
        """
        self._jwks_client = jwks_client
        self._issuer = issuer
        self._client_id = client_id

    def verificar(self, token: str) -> ClienteAutenticado:
        """Valida o access token e devolve a identidade autenticada.

        Args:
            token: Access token JWT (sem o prefixo "Bearer").

        Returns:
            Identidade do cliente derivada das claims (`sub`, `cognito:groups`).

        Raises:
            TokenInvalidoError: Se o token for invalido, expirado, mal-assinado,
                nao for um access token, ou for de outro App Client.
        """
        try:
            chave = self._jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token,
                chave.key,
                algorithms=_ALGORITMOS,
                issuer=self._issuer,
                options={"require": ["exp", "iss", "sub"], "verify_aud": False},
            )
        except jwt.PyJWTError as exc:
            raise TokenInvalidoError from exc

        if claims.get("token_use") != _TOKEN_USE_ESPERADO:
            raise TokenInvalidoError
        if claims.get("client_id") != self._client_id:
            raise TokenInvalidoError

        grupos = tuple(claims.get("cognito:groups") or ())
        return ClienteAutenticado(sub=claims["sub"], grupos=grupos)
