"""Value Object Cpf (normalizado e validado por digitos verificadores)."""

from pydantic import BaseModel, ConfigDict, field_validator

_TAMANHO_CPF = 11


def _calcular_digito_verificador(digitos: str, pesos: range) -> int:
    """Calcula um digito verificador do CPF (algoritmo modulo 11).

    Args:
        digitos: Digitos ja validados usados no calculo.
        pesos: Pesos decrescentes aplicados a cada digito.

    Returns:
        Digito verificador esperado (0 a 9).
    """
    soma = sum(int(digito) * peso for digito, peso in zip(digitos, pesos, strict=True))
    resto = soma % 11
    return 0 if resto < 2 else 11 - resto


class Cpf(BaseModel):
    """CPF valido do cliente, sempre armazenado NORMALIZADO (somente digitos).

    A normalizacao antes de qualquer persistencia e um controle de
    integridade: garante um formato canonico unico (``123.456.789-09`` e
    ``12345678909`` sao o mesmo CPF).

    Atributos:
        valor: CPF normalizado (11 digitos, verificadores validos).
    """

    model_config = ConfigDict(frozen=True)

    valor: str

    @field_validator("valor")
    @classmethod
    def _normalizar_e_validar(cls, valor: str) -> str:
        """Normaliza para digitos-apenas e valida os digitos verificadores.

        Args:
            valor: CPF em qualquer formatacao usual.

        Returns:
            CPF normalizado (somente digitos).

        Raises:
            ValueError: Se o CPF nao tiver 11 digitos, for uma sequencia
                repetida ou tiver digitos verificadores invalidos.
        """
        digitos = "".join(caractere for caractere in valor if caractere.isdigit())
        if len(digitos) != _TAMANHO_CPF:
            raise ValueError("CPF deve conter 11 digitos.")
        if digitos == digitos[0] * _TAMANHO_CPF:
            raise ValueError("CPF invalido.")

        primeiro = _calcular_digito_verificador(digitos[:9], range(10, 1, -1))
        segundo = _calcular_digito_verificador(digitos[:10], range(11, 1, -1))
        if digitos[9] != str(primeiro) or digitos[10] != str(segundo):
            raise ValueError("CPF invalido.")
        return digitos
