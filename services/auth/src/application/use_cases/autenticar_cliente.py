"""Caso de uso: autenticar um cliente."""

from src.application.dtos.auth import AutenticarClienteCommand, TokensDTO
from src.application.ports.identity_provider import IdentityProvider
from src.domain.value_objects import Email, Senha


class AutenticarCliente:
    """Autentica um cliente e retorna os tokens emitidos pelo provedor."""

    def __init__(self, identity: IdentityProvider) -> None:
        """Recebe o provedor de identidade por injecao.

        Args:
            identity: Port do provedor de identidade.
        """
        self._identity = identity

    async def executar(self, comando: AutenticarClienteCommand) -> TokensDTO:
        """Autentica o cliente e devolve os tokens.

        Args:
            comando: E-mail e senha do cliente.

        Returns:
            DTO com os tokens emitidos pelo provedor.
        """
        return await self._identity.autenticar(
            Email(valor=comando.email),
            Senha(valor=comando.senha),
        )
