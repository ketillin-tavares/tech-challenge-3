"""Port: provedor de identidade (registro e autenticacao de clientes)."""

from abc import ABC, abstractmethod

from src.application.dtos.auth import TokensDTO
from src.domain.value_objects import Email, Senha


class IdentityProvider(ABC):
    """Contrato do provedor de identidade externo (driven adapter).

    Implementado por um adapter concreto (ex.: Cognito). As camadas internas
    nunca conhecem o provedor concreto, apenas este contrato.
    """

    @abstractmethod
    async def registrar(self, email: Email, senha: Senha) -> str:
        """Registra um novo cliente.

        Args:
            email: E-mail do cliente.
            senha: Senha do cliente.

        Returns:
            Identificador opaco do cliente (`sub`).

        Raises:
            ClienteJaExisteError: Se o e-mail ja estiver cadastrado.
        """
        ...

    @abstractmethod
    async def autenticar(self, email: Email, senha: Senha) -> TokensDTO:
        """Autentica um cliente e emite tokens.

        Args:
            email: E-mail do cliente.
            senha: Senha do cliente.

        Returns:
            Tokens de acesso emitidos pelo provedor.

        Raises:
            CredenciaisInvalidasError: Se as credenciais forem invalidas.
        """
        ...
