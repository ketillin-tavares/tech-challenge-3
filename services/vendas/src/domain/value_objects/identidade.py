"""Value Object de identidade derivada do token (ClienteAutenticado)."""

from pydantic import BaseModel, ConfigDict


class ClienteAutenticado(BaseModel):
    """Identidade de um cliente derivada do JWT validado.

    Nao carrega PII nem conhecimento de HTTP/JWT: apenas o identificador opaco
    (`sub`) e os grupos do token, usados para autorizacao.

    Atributos:
        sub: Identificador opaco do cliente (claim `sub` do JWT).
        grupos: Grupos aos quais o cliente pertence (claim `cognito:groups`).
    """

    model_config = ConfigDict(frozen=True)

    sub: str
    grupos: tuple[str, ...] = ()

    def tem_grupo(self, grupo: str) -> bool:
        """Indica se a identidade pertence a um grupo.

        Args:
            grupo: Nome do grupo a verificar.

        Returns:
            True se o cliente pertence ao grupo informado.
        """
        return grupo in self.grupos
