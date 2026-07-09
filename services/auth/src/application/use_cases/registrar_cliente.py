"""Caso de uso: registrar um novo cliente."""

from src.application.dtos.auth import ClienteRegistradoDTO, RegistrarClienteCommand
from src.application.ports.identity_provider import IdentityProvider
from src.domain.value_objects import Email, Senha


class RegistrarCliente:
    """Registra um cliente no provedor de identidade."""

    def __init__(self, identity: IdentityProvider) -> None:
        """Recebe o provedor de identidade por injecao.

        Args:
            identity: Port do provedor de identidade.
        """
        self._identity = identity

    async def executar(self, comando: RegistrarClienteCommand) -> ClienteRegistradoDTO:
        """Registra o cliente e retorna seu identificador.

        Os VOs `Email`/`Senha` sao construidos aqui; valores invalidos levantam
        `pydantic.ValidationError`, tratada na borda (422).

        Args:
            comando: E-mail e senha do cliente.

        Returns:
            DTO com o identificador (`sub`) do cliente registrado.
        """
        sub = await self._identity.registrar(
            Email(valor=comando.email),
            Senha(valor=comando.senha),
        )
        return ClienteRegistradoDTO(sub=sub)
