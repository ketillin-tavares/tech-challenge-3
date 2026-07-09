"""Gateway concreto do IdentityProvider usando AWS Cognito (boto3)."""

from typing import Any

from botocore.exceptions import ClientError
from fastapi.concurrency import run_in_threadpool

from src.application.dtos.auth import TokensDTO
from src.application.ports.identity_provider import IdentityProvider
from src.domain.exceptions import ClienteJaExisteError, CredenciaisInvalidasError
from src.domain.value_objects import Email, Senha

_ERROS_CREDENCIAIS = {"NotAuthorizedException", "UserNotFoundException"}


class CognitoIdentityProvider(IdentityProvider):
    """Implementa o IdentityProvider sobre o Cognito User Pool.

    O boto3 e sincrono; as chamadas sao executadas em threadpool para nao
    bloquear o event loop. Erros do Cognito (`ClientError`) sao traduzidos
    para excecoes de dominio, sem vazar detalhes do provedor.
    """

    def __init__(self, client: Any, client_id: str, user_pool_id: str) -> None:
        """Recebe o cliente boto3, o id do App Client e o id do User Pool.

        Args:
            client: Cliente boto3 `cognito-idp`.
            client_id: Id do App Client do Cognito.
            user_pool_id: Id do User Pool (necessario para confirmar o cadastro).
        """
        self._client = client
        self._client_id = client_id
        self._user_pool_id = user_pool_id

    async def registrar(self, email: Email, senha: Senha) -> str:
        """Registra e confirma o cliente (auto-confirmacao via admin).

        O `SignUp` cria o usuario como UNCONFIRMED; em seguida
        `AdminConfirmSignUp` o confirma, para que o login funcione sem etapa de
        codigo por e-mail (decisao de dominio: clientes auto-confirmados).

        Args:
            email: E-mail do cliente.
            senha: Senha do cliente.

        Returns:
            Identificador opaco do cliente (`sub`).

        Raises:
            ClienteJaExisteError: Se o e-mail ja estiver cadastrado.
        """
        try:
            resposta = await run_in_threadpool(
                self._client.sign_up,
                ClientId=self._client_id,
                Username=email.valor,
                Password=senha.valor,
                UserAttributes=[{"Name": "email", "Value": email.valor}],
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "UsernameExistsException":
                raise ClienteJaExisteError(email.valor) from exc
            raise
        await run_in_threadpool(
            self._client.admin_confirm_sign_up,
            UserPoolId=self._user_pool_id,
            Username=email.valor,
        )
        return resposta["UserSub"]

    async def autenticar(self, email: Email, senha: Senha) -> TokensDTO:
        """Autentica via `InitiateAuth` (fluxo USER_PASSWORD_AUTH).

        Args:
            email: E-mail do cliente.
            senha: Senha do cliente.

        Returns:
            Tokens emitidos pelo Cognito.

        Raises:
            CredenciaisInvalidasError: Se as credenciais forem invalidas.
        """
        try:
            resposta = await run_in_threadpool(
                self._client.initiate_auth,
                ClientId=self._client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": email.valor, "PASSWORD": senha.valor},
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] in _ERROS_CREDENCIAIS:
                raise CredenciaisInvalidasError from exc
            raise
        resultado = resposta["AuthenticationResult"]
        return TokensDTO(
            id_token=resultado["IdToken"],
            access_token=resultado["AccessToken"],
            refresh_token=resultado["RefreshToken"],
            token_type=resultado["TokenType"],
            expires_in=resultado["ExpiresIn"],
        )
