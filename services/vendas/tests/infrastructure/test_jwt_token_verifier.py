"""Testes unitarios para JwtTokenVerifier (adapter de verificacao JWT do Cognito)."""

from datetime import UTC, datetime, timedelta
from typing import cast
from unittest.mock import Mock

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWKClient

from src.domain.exceptions import TokenInvalidoError
from src.domain.value_objects import ClienteAutenticado
from src.infrastructure.auth.jwt_token_verifier import JwtTokenVerifier


@pytest.mark.unit
class TestJwtTokenVerifier:
    """Testes do verificador de JWT do Cognito."""

    @pytest.fixture
    def chave_privada(self) -> rsa.RSAPrivateKey:
        """Gera um par RSA de teste."""
        return rsa.generate_private_key(public_exponent=65537, key_size=2048)

    @pytest.fixture
    def jwks_mock(self, chave_privada: rsa.RSAPrivateKey) -> Mock:
        """Mock do cliente JWKS que devolve a chave publica."""
        chave_assinante = Mock()
        chave_assinante.key = chave_privada.public_key()
        jwks = Mock(spec=PyJWKClient)
        jwks.get_signing_key_from_jwt.return_value = chave_assinante
        return jwks

    @pytest.fixture
    def verifier(self, jwks_mock: Mock) -> JwtTokenVerifier:
        """Cria uma instancia do verificador com mocks."""
        return JwtTokenVerifier(
            cast(PyJWKClient, jwks_mock),
            issuer="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test000",
            client_id="testclientid",
        )

    def _criar_token(
        self,
        chave_privada: rsa.RSAPrivateKey,
        *,
        token_use: str = "access",
        grupos: list[str] | None = None,
        expirado: bool = False,
    ) -> str:
        """Cria um token JWT assinado para teste.

        Args:
            chave_privada: Chave privada para assinar.
            token_use: Claim token_use (padrao "access").
            grupos: Lista de grupos para cognito:groups (padrao None).
            expirado: Se True, exp sera no passado.

        Returns:
            Token JWT assinado.
        """
        agora = datetime.now(UTC)
        exp = agora - timedelta(hours=1) if expirado else agora + timedelta(hours=1)
        claims: dict[str, str | datetime | list[str]] = {
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test000",
            "sub": "cliente-123",
            "client_id": "testclientid",
            "token_use": token_use,
            "exp": exp,
            "iat": agora,
        }
        if grupos:
            claims["cognito:groups"] = grupos
        return jwt.encode(claims, chave_privada, algorithm="RS256")

    def test_verificar_token_valido_sem_grupos(
        self, verifier: JwtTokenVerifier, chave_privada: rsa.RSAPrivateKey
    ) -> None:
        """Retorna ClienteAutenticado vazio sem grupos."""
        token = self._criar_token(chave_privada)

        resultado = verifier.verificar(token)

        assert isinstance(resultado, ClienteAutenticado)
        assert resultado.sub == "cliente-123"
        assert resultado.grupos == ()

    def test_verificar_token_valido_com_grupos(
        self, verifier: JwtTokenVerifier, chave_privada: rsa.RSAPrivateKey
    ) -> None:
        """Extrai grupos cognito:groups corretamente."""
        token = self._criar_token(chave_privada, grupos=["admin"])

        resultado = verifier.verificar(token)

        assert resultado.sub == "cliente-123"
        assert resultado.grupos == ("admin",)

    def test_verificar_token_valido_com_multiplos_grupos(
        self, verifier: JwtTokenVerifier, chave_privada: rsa.RSAPrivateKey
    ) -> None:
        """Extrai multiplos grupos como tuple."""
        token = self._criar_token(chave_privada, grupos=["admin", "vendedor", "usuario"])

        resultado = verifier.verificar(token)

        assert resultado.sub == "cliente-123"
        assert resultado.grupos == ("admin", "vendedor", "usuario")

    def test_verificar_token_expirado(
        self, verifier: JwtTokenVerifier, chave_privada: rsa.RSAPrivateKey
    ) -> None:
        """Arrange: token com exp no passado. Act: verificar. Assert: levanta TokenInvalidoError."""
        token = self._criar_token(chave_privada, expirado=True)

        with pytest.raises(TokenInvalidoError):
            verifier.verificar(token)

    def test_verificar_token_use_id_levanta_erro(
        self, verifier: JwtTokenVerifier, chave_privada: rsa.RSAPrivateKey
    ) -> None:
        """Rejeita token_use id (deve ser access)."""
        token = self._criar_token(chave_privada, token_use="id")

        with pytest.raises(TokenInvalidoError):
            verifier.verificar(token)

    def test_verificar_token_use_ausente_levanta_erro(
        self, verifier: JwtTokenVerifier, chave_privada: rsa.RSAPrivateKey
    ) -> None:
        """Arrange: token sem token_use. Act: verificar. Assert: levanta TokenInvalidoError."""
        agora = datetime.now(UTC)
        claims = {
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test000",
            "sub": "cliente-123",
            "client_id": "testclientid",
            "exp": agora + timedelta(hours=1),
            "iat": agora,
        }
        token = jwt.encode(claims, chave_privada, algorithm="RS256")

        with pytest.raises(TokenInvalidoError):
            verifier.verificar(token)

    def test_verificar_issuer_invalido_levanta_erro(
        self, jwks_mock: Mock, chave_privada: rsa.RSAPrivateKey
    ) -> None:
        """Rejeita token com issuer incorreto."""
        verifier = JwtTokenVerifier(
            cast(PyJWKClient, jwks_mock),
            issuer="https://wrong-issuer.com",
            client_id="testclientid",
        )
        agora = datetime.now(UTC)
        claims = {
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test000",
            "sub": "cliente-123",
            "client_id": "testclientid",
            "token_use": "access",
            "exp": agora + timedelta(hours=1),
            "iat": agora,
        }
        token = jwt.encode(claims, chave_privada, algorithm="RS256")

        with pytest.raises(TokenInvalidoError):
            verifier.verificar(token)

    def test_verificar_client_id_invalido_levanta_erro(
        self, jwks_mock: Mock, chave_privada: rsa.RSAPrivateKey
    ) -> None:
        """Rejeita token com client_id incorreto."""
        verifier = JwtTokenVerifier(
            cast(PyJWKClient, jwks_mock),
            issuer="https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test000",
            client_id="expected",
        )
        agora = datetime.now(UTC)
        claims = {
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_test000",
            "sub": "cliente-123",
            "client_id": "outro",
            "token_use": "access",
            "exp": agora + timedelta(hours=1),
            "iat": agora,
        }
        token = jwt.encode(claims, chave_privada, algorithm="RS256")

        with pytest.raises(TokenInvalidoError):
            verifier.verificar(token)

    def test_verificar_token_malformado_levanta_erro(self, verifier: JwtTokenVerifier) -> None:
        """Arrange: token malformado. Act: verificar. Assert: levanta TokenInvalidoError."""
        token = "nao.e.um.token.jwt"

        with pytest.raises(TokenInvalidoError):
            verifier.verificar(token)
