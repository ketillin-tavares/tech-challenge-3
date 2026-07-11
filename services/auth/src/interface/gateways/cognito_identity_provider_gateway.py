"""Gateway concreto do IdentityProvider usando AWS Cognito (boto3).

Politica de PII: nenhum valor de atributo do Cognito (CPF, email, nome) e
interpolado em excecoes ou logs -- as excecoes de dominio tem mensagens fixas
e a causa original fica apenas no traceback interno (`raise ... from exc`).
"""

from typing import Any

from botocore.exceptions import ClientError
from fastapi.concurrency import run_in_threadpool

from src.application.dtos.auth import PerfilClienteDTO, TokensDTO
from src.application.ports.identity_provider import IdentityProvider
from src.domain.exceptions import (
    ClienteJaExisteError,
    CredenciaisInvalidasError,
    TokenInvalidoError,
)
from src.domain.value_objects import Cpf, Email, Senha

_ERROS_CREDENCIAIS = {"NotAuthorizedException", "UserNotFoundException"}
_ATRIBUTO_CPF = "custom:cpf"


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
            user_pool_id: Id do User Pool (confirmacao de cadastro e ListUsers).
        """
        self._client = client
        self._client_id = client_id
        self._user_pool_id = user_pool_id

    async def registrar(self, email: Email, senha: Senha, nome: str, cpf: Cpf) -> str:
        """Registra e confirma o cliente (auto-confirmacao via admin).

        O `SignUp` cria o usuario como UNCONFIRMED ja com o perfil completo
        (email + name + custom:cpf, numa unica chamada atomica); em seguida
        `AdminConfirmSignUp` o confirma, para que o login funcione sem etapa
        de codigo por e-mail (decisao de dominio: clientes auto-confirmados).

        Args:
            email: E-mail do cliente.
            senha: Senha do cliente.
            nome: Nome completo do cliente.
            cpf: CPF validado e normalizado (VO).

        Returns:
            Identificador opaco do cliente (`sub`).

        Raises:
            ClienteJaExisteError: Se os dados ja estiverem cadastrados.
        """
        try:
            resposta = await run_in_threadpool(
                self._client.sign_up,
                ClientId=self._client_id,
                Username=email.valor,
                Password=senha.valor,
                UserAttributes=[
                    {"Name": "email", "Value": email.valor},
                    {"Name": "name", "Value": nome},
                    {"Name": _ATRIBUTO_CPF, "Value": cpf.valor},
                ],
            )
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "UsernameExistsException":
                raise ClienteJaExisteError from exc
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

    async def obter_perfil_proprio(self, access_token: str) -> PerfilClienteDTO:
        """Retorna o perfil do dono do token via `GetUser` (menor privilegio).

        `GetUser` e autorizado pelo PROPRIO access token do cliente: nenhuma
        credencial administrativa (IAM) participa deste read-path.

        Args:
            access_token: Access token do proprio cliente.

        Returns:
            Perfil do cliente autenticado.

        Raises:
            TokenInvalidoError: Se o Cognito rejeitar o token.
        """
        try:
            resposta = await run_in_threadpool(
                self._client.get_user,
                AccessToken=access_token,
            )
        except ClientError as exc:
            raise TokenInvalidoError from exc
        return self._atributos_para_perfil(resposta["UserAttributes"])

    async def obter_perfil_por_sub(self, sub: str) -> PerfilClienteDTO | None:
        """Retorna o perfil pelo `sub` via `ListUsers` com filtro.

        O atributo padrao `sub` e filtravel por contrato documentado da AWS
        (diferente do username, cuja igualdade com o sub NAO e garantida).

        Args:
            sub: Identificador opaco do cliente.

        Returns:
            Perfil do cliente, ou None quando o `sub` nao existe.
        """
        # O sub e opaco (UUID); aspas sao removidas para nao quebrar a
        # sintaxe do filtro do ListUsers (injecao de filtro).
        sub_sanitizado = sub.replace('"', "")
        resposta = await run_in_threadpool(
            self._client.list_users,
            UserPoolId=self._user_pool_id,
            Filter=f'sub = "{sub_sanitizado}"',
            Limit=1,
        )
        usuarios = resposta.get("Users", [])
        if not usuarios:
            return None
        return self._atributos_para_perfil(usuarios[0]["Attributes"])

    @staticmethod
    def _atributos_para_perfil(atributos: list[dict[str, str]]) -> PerfilClienteDTO:
        """Converte a lista de atributos do Cognito em `PerfilClienteDTO`.

        Atributos ausentes (usuarios legados sem nome/CPF) viram None.

        Args:
            atributos: Lista de pares Name/Value do Cognito.

        Returns:
            Perfil do cliente com os campos mapeados.
        """
        valores = {atributo["Name"]: atributo["Value"] for atributo in atributos}
        return PerfilClienteDTO(
            sub=valores["sub"],
            email=valores.get("email", ""),
            nome=valores.get("name"),
            cpf=valores.get(_ATRIBUTO_CPF),
        )
