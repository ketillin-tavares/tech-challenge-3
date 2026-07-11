"""Port: provedor de identidade (registro, autenticacao e perfil de clientes)."""

from abc import ABC, abstractmethod

from src.application.dtos.auth import PerfilClienteDTO, TokensDTO
from src.domain.value_objects import Cpf, Email, Senha


class IdentityProvider(ABC):
    """Contrato do provedor de identidade externo (driven adapter).

    Implementado por um adapter concreto (ex.: Cognito). As camadas internas
    nunca conhecem o provedor concreto, apenas este contrato. O perfil do
    cliente (nome, CPF) vive exclusivamente no provedor -- este servico nao
    possui banco de dados.
    """

    @abstractmethod
    async def registrar(self, email: Email, senha: Senha, nome: str, cpf: Cpf) -> str:
        """Registra um novo cliente com seu perfil (nome e CPF).

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

    @abstractmethod
    async def obter_perfil_proprio(self, access_token: str) -> PerfilClienteDTO:
        """Retorna o perfil do dono do access token (menor privilegio).

        Args:
            access_token: Access token do proprio cliente.

        Returns:
            Perfil do cliente autenticado.

        Raises:
            TokenInvalidoError: Se o token for rejeitado pelo provedor.
        """
        ...

    @abstractmethod
    async def obter_perfil_por_sub(self, sub: str) -> PerfilClienteDTO | None:
        """Retorna o perfil de um cliente pelo `sub`, ou None se inexistente.

        Args:
            sub: Identificador opaco do cliente.

        Returns:
            Perfil do cliente, ou None quando o `sub` nao existe.
        """
        ...
