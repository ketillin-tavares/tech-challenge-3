"""Value Object Ano."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, field_validator

ANO_MINIMO = 1900


class Ano(BaseModel):
    """Ano de fabricacao plausivel: entre 1900 e o proximo ano.

    Atributos:
        valor: Ano de quatro digitos dentro do intervalo permitido.
    """

    model_config = ConfigDict(frozen=True)

    valor: int

    @field_validator("valor")
    @classmethod
    def _validar_intervalo(cls, valor: int) -> int:
        """Garante que o ano esta entre `ANO_MINIMO` e o ano atual + 1.

        Args:
            valor: Ano informado.

        Returns:
            O proprio ano, se valido.

        Raises:
            ValueError: Se o ano estiver fora do intervalo permitido.
        """
        limite_superior = datetime.now(UTC).year + 1
        if not (ANO_MINIMO <= valor <= limite_superior):
            raise ValueError(f"Ano deve estar entre {ANO_MINIMO} e {limite_superior}.")
        return valor
