"""Caso de uso: consultar o proprio perfil (dono do access token)."""

from src.application.dtos.auth import PerfilClienteDTO
from src.application.ports.identity_provider import IdentityProvider


class ObterPerfilProprio:
    """Consulta o perfil do cliente autenticado no provedor de identidade.

    Usa o PROPRIO access token do cliente na consulta (menor privilegio):
    nenhuma credencial administrativa participa deste read-path.
    """

    def __init__(self, identity: IdentityProvider) -> None:
        """Recebe o provedor de identidade por injecao.

        Args:
            identity: Port do provedor de identidade.
        """
        self._identity = identity

    async def executar(self, access_token: str) -> PerfilClienteDTO:
        """Retorna o perfil do dono do token.

        Args:
            access_token: Access token do proprio cliente.

        Returns:
            Perfil do cliente (nome/CPF podem ser None em usuarios legados).

        Raises:
            TokenInvalidoError: Se o provedor rejeitar o token.
        """
        return await self._identity.obter_perfil_proprio(access_token)
