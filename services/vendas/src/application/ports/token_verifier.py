"""Port: verificador de token JWT (produz a identidade autenticada)."""

from abc import ABC, abstractmethod

from src.domain.value_objects import ClienteAutenticado


class TokenVerifier(ABC):
    """Contrato de verificacao de token de acesso.

    Implementado por um adapter de infraestrutura (ex.: validacao via JWKS do
    Cognito). Converte um token opaco em uma identidade de dominio.
    """

    @abstractmethod
    def verificar(self, token: str) -> ClienteAutenticado:
        """Valida o token e retorna a identidade autenticada.

        Args:
            token: Token JWT (sem o prefixo "Bearer").

        Returns:
            Identidade do cliente derivada das claims.

        Raises:
            TokenInvalidoError: Se o token for invalido, expirado ou mal-assinado.
        """
        ...
