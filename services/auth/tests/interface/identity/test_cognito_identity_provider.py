"""Testes de CognitoIdentityProvider (adapter de identidade via AWS Cognito)."""

from unittest.mock import Mock

import pytest
from botocore.exceptions import ClientError

from src.application.dtos.auth import TokensDTO
from src.domain.exceptions import ClienteJaExisteError, CredenciaisInvalidasError
from src.domain.value_objects import Cpf, Email, Senha
from src.interface.gateways.cognito_identity_provider_gateway import CognitoIdentityProvider


@pytest.mark.unit
class TestCognitoIdentityProvider:
    """Testes do provedor de identidade Cognito."""

    @pytest.fixture
    def cognito_client_mock(self) -> Mock:
        """Mock do cliente boto3 cognito-idp."""
        return Mock()

    @pytest.fixture
    def provider(self, cognito_client_mock: Mock) -> CognitoIdentityProvider:
        """Cria uma instancia do provedor com mock do cliente."""
        return CognitoIdentityProvider(
            cognito_client_mock, client_id="testclientid", user_pool_id="us-east-1_test000"
        )

    @pytest.fixture
    def email(self) -> Email:
        """Email de teste valido."""
        return Email(valor="cliente@example.com")

    @pytest.fixture
    def senha(self) -> Senha:
        """Senha de teste valida."""
        return Senha(valor="senhaSegura1")

    @pytest.fixture
    def cpf(self) -> Cpf:
        """CPF de teste valido."""
        return Cpf(valor="12345678909")

    async def test_registrar_sucesso(
        self,
        provider: CognitoIdentityProvider,
        cognito_client_mock: Mock,
        email: Email,
        senha: Senha,
        cpf: Cpf,
    ) -> None:
        """Registra cliente e retorna sub do Cognito."""
        cognito_client_mock.sign_up.return_value = {"UserSub": "sub-1"}

        resultado = await provider.registrar(email, senha, "João Silva", cpf)

        assert resultado == "sub-1"
        cognito_client_mock.sign_up.assert_called_once()
        call_kwargs = cognito_client_mock.sign_up.call_args[1]
        assert call_kwargs["ClientId"] == "testclientid"
        assert call_kwargs["Username"] == "cliente@example.com"
        assert call_kwargs["Password"] == "senhaSegura1"
        # Verifica que os atributos do usuario incluem email, nome e cpf
        user_attrs = {attr["Name"]: attr["Value"] for attr in call_kwargs["UserAttributes"]}
        assert user_attrs["email"] == "cliente@example.com"
        assert user_attrs["name"] == "João Silva"
        assert user_attrs["custom:cpf"] == cpf.valor
        cognito_client_mock.admin_confirm_sign_up.assert_called_once_with(
            UserPoolId="us-east-1_test000", Username="cliente@example.com"
        )

    async def test_registrar_usuario_ja_existe(
        self,
        provider: CognitoIdentityProvider,
        cognito_client_mock: Mock,
        email: Email,
        senha: Senha,
        cpf: Cpf,
    ) -> None:
        """Rejeita email ja existente com ClienteJaExisteError."""
        erro = ClientError(
            {"Error": {"Code": "UsernameExistsException", "Message": "User already exists"}},
            "SignUp",
        )
        cognito_client_mock.sign_up.side_effect = erro

        with pytest.raises(ClienteJaExisteError):
            await provider.registrar(email, senha, "João Silva", cpf)

        cognito_client_mock.admin_confirm_sign_up.assert_not_called()

    async def test_registrar_outro_erro_cognito(
        self,
        provider: CognitoIdentityProvider,
        cognito_client_mock: Mock,
        email: Email,
        senha: Senha,
        cpf: Cpf,
    ) -> None:
        """Propaga outros ClientErrors do Cognito."""
        erro = ClientError(
            {"Error": {"Code": "InternalErrorException", "Message": "Server error"}},
            "SignUp",
        )
        cognito_client_mock.sign_up.side_effect = erro

        with pytest.raises(ClientError):
            await provider.registrar(email, senha, "João Silva", cpf)

        cognito_client_mock.admin_confirm_sign_up.assert_not_called()

    async def test_autenticar_sucesso(
        self,
        provider: CognitoIdentityProvider,
        cognito_client_mock: Mock,
        email: Email,
        senha: Senha,
    ) -> None:
        """Autentica e retorna TokensDTO com tokens validos."""
        cognito_client_mock.initiate_auth.return_value = {
            "AuthenticationResult": {
                "IdToken": "id-token-123",
                "AccessToken": "access-token-456",
                "RefreshToken": "refresh-token-789",
                "TokenType": "Bearer",
                "ExpiresIn": 3600,
            }
        }

        resultado = await provider.autenticar(email, senha)

        assert isinstance(resultado, TokensDTO)
        assert resultado.id_token == "id-token-123"
        assert resultado.access_token == "access-token-456"
        assert resultado.refresh_token == "refresh-token-789"
        assert resultado.token_type == "Bearer"
        assert resultado.expires_in == 3600
        cognito_client_mock.initiate_auth.assert_called_once_with(
            ClientId="testclientid",
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": "cliente@example.com", "PASSWORD": "senhaSegura1"},
        )

    async def test_autenticar_credenciais_invalidas_not_authorized(
        self,
        provider: CognitoIdentityProvider,
        cognito_client_mock: Mock,
        email: Email,
        senha: Senha,
    ) -> None:
        """Rejeita NotAuthorizedException com CredenciaisInvalidasError."""
        erro = ClientError(
            {
                "Error": {
                    "Code": "NotAuthorizedException",
                    "Message": "Invalid credentials",
                }
            },
            "InitiateAuth",
        )
        cognito_client_mock.initiate_auth.side_effect = erro

        with pytest.raises(CredenciaisInvalidasError):
            await provider.autenticar(email, senha)

    async def test_autenticar_credenciais_invalidas_user_not_found(
        self,
        provider: CognitoIdentityProvider,
        cognito_client_mock: Mock,
        email: Email,
        senha: Senha,
    ) -> None:
        """Rejeita UserNotFoundException com CredenciaisInvalidasError."""
        erro = ClientError(
            {
                "Error": {
                    "Code": "UserNotFoundException",
                    "Message": "User does not exist",
                }
            },
            "InitiateAuth",
        )
        cognito_client_mock.initiate_auth.side_effect = erro

        with pytest.raises(CredenciaisInvalidasError):
            await provider.autenticar(email, senha)

    async def test_autenticar_outro_erro_cognito(
        self,
        provider: CognitoIdentityProvider,
        cognito_client_mock: Mock,
        email: Email,
        senha: Senha,
    ) -> None:
        """Propaga outros ClientErrors do Cognito."""
        erro = ClientError(
            {
                "Error": {
                    "Code": "InternalErrorException",
                    "Message": "Server error",
                }
            },
            "InitiateAuth",
        )
        cognito_client_mock.initiate_auth.side_effect = erro

        with pytest.raises(ClientError):
            await provider.autenticar(email, senha)

    async def test_obter_perfil_proprio_sucesso(
        self, provider: CognitoIdentityProvider, cognito_client_mock: Mock
    ) -> None:
        """Obtem perfil proprio com get_user."""
        from src.application.dtos.auth import PerfilClienteDTO

        cognito_client_mock.get_user.return_value = {
            "Username": "cliente@example.com",
            "UserAttributes": [
                {"Name": "sub", "Value": "sub-123"},
                {"Name": "email", "Value": "cliente@example.com"},
                {"Name": "name", "Value": "João Silva"},
                {"Name": "custom:cpf", "Value": "12345678909"},
            ],
        }

        resultado = await provider.obter_perfil_proprio("token-abc")

        assert isinstance(resultado, PerfilClienteDTO)
        assert resultado.sub == "sub-123"
        assert resultado.nome == "João Silva"
        assert resultado.cpf == "12345678909"

    async def test_obter_perfil_proprio_token_invalido(
        self, provider: CognitoIdentityProvider, cognito_client_mock: Mock
    ) -> None:
        """Token invalido em get_user levanta TokenInvalidoError."""
        from src.domain.exceptions import TokenInvalidoError

        erro = ClientError(
            {"Error": {"Code": "NotAuthorizedException", "Message": "Token invalid"}},
            "GetUser",
        )
        cognito_client_mock.get_user.side_effect = erro

        with pytest.raises(TokenInvalidoError):
            await provider.obter_perfil_proprio("token-inválido")

    async def test_obter_perfil_por_sub_sucesso(
        self, provider: CognitoIdentityProvider, cognito_client_mock: Mock
    ) -> None:
        """Obtem perfil por sub com list_users."""

        cognito_client_mock.list_users.return_value = {
            "Users": [
                {
                    "Username": "cliente@example.com",
                    "Attributes": [
                        {"Name": "sub", "Value": "sub-123"},
                        {"Name": "email", "Value": "cliente@example.com"},
                        {"Name": "name", "Value": "João Silva"},
                        {"Name": "custom:cpf", "Value": "12345678909"},
                    ],
                }
            ]
        }

        resultado = await provider.obter_perfil_por_sub("sub-123")

        assert resultado is not None
        assert resultado.sub == "sub-123"
        assert resultado.nome == "João Silva"

    async def test_obter_perfil_por_sub_nao_encontrado(
        self, provider: CognitoIdentityProvider, cognito_client_mock: Mock
    ) -> None:
        """Sub nao encontrado retorna None."""
        cognito_client_mock.list_users.return_value = {"Users": []}

        resultado = await provider.obter_perfil_por_sub("sub-inexistente")

        assert resultado is None

    async def test_obter_perfil_por_sub_legado_sem_cpf(
        self, provider: CognitoIdentityProvider, cognito_client_mock: Mock
    ) -> None:
        """Usuario legado sem cpf/nome retorna None para esses campos."""

        cognito_client_mock.list_users.return_value = {
            "Users": [
                {
                    "Username": "cliente@example.com",
                    "Attributes": [
                        {"Name": "sub", "Value": "sub-456"},
                        {"Name": "email", "Value": "cliente@example.com"},
                    ],
                }
            ]
        }

        resultado = await provider.obter_perfil_por_sub("sub-456")

        assert resultado is not None
        assert resultado.cpf is None
        assert resultado.nome is None
        assert resultado.email == "cliente@example.com"
