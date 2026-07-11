"""Caso de uso: consultar o perfil de um cliente pelo `sub` (admin)."""

from src.application.dtos.auth import PerfilClienteDTO
from src.application.ports.identity_provider import IdentityProvider
from src.domain.exceptions import ClienteNaoEncontradoError


class ObterPerfilPorSub:
    """Consulta o perfil de qualquer cliente pelo identificador opaco.

    Responde "quem comprou este veiculo?": o servico de vendas guarda apenas o
    `sub` na venda, e este caso de uso resolve o `sub` para nome/CPF/email.
    A autorizacao (grupo admin) e aplicada na borda.
    """

    def __init__(self, identity: IdentityProvider) -> None:
        """Recebe o provedor de identidade por injecao.

        Args:
            identity: Port do provedor de identidade.
        """
        self._identity = identity

    async def executar(self, sub: str) -> PerfilClienteDTO:
        """Retorna o perfil do cliente identificado por `sub`.

        Args:
            sub: Identificador opaco do cliente (mesmo valor gravado na venda).

        Returns:
            Perfil do cliente (nome/CPF podem ser None em usuarios legados).

        Raises:
            ClienteNaoEncontradoError: Se nao existir cliente com esse `sub`.
        """
        perfil = await self._identity.obter_perfil_por_sub(sub)
        if perfil is None:
            raise ClienteNaoEncontradoError
        return perfil
