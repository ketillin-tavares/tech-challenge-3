"""Caso de uso: registrar um novo cliente."""

from src.application.dtos.auth import ClienteRegistradoDTO, RegistrarClienteCommand
from src.application.ports.identity_provider import IdentityProvider
from src.domain.value_objects import Cpf, Email, Senha


class RegistrarCliente:
    """Registra um cliente (credenciais + perfil) no provedor de identidade."""

    def __init__(self, identity: IdentityProvider) -> None:
        """Recebe o provedor de identidade por injecao.

        Args:
            identity: Port do provedor de identidade.
        """
        self._identity = identity

    async def executar(self, comando: RegistrarClienteCommand) -> ClienteRegistradoDTO:
        """Registra o cliente e retorna seu identificador e perfil.

        Os VOs `Email`/`Senha`/`Cpf` sao construidos aqui; valores invalidos
        levantam `pydantic.ValidationError`, tratada na borda (422). O CPF e
        normalizado (somente digitos) pelo VO antes de chegar ao provedor.

        Args:
            comando: E-mail, senha, nome e CPF do cliente.

        Returns:
            DTO com o identificador (`sub`), nome e CPF normalizado.
        """
        cpf = Cpf(valor=comando.cpf)
        sub = await self._identity.registrar(
            Email(valor=comando.email),
            Senha(valor=comando.senha),
            comando.nome,
            cpf,
        )
        return ClienteRegistradoDTO(sub=sub, nome=comando.nome, cpf=cpf.valor)
