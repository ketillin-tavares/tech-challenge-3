"""Value Objects de credenciais do contexto de Identidade/Auth (Email, Senha)."""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Email(BaseModel):
    """Endereco de e-mail valido do cliente.

    Atributos:
        valor: E-mail validado (formato RFC).
    """

    model_config = ConfigDict(frozen=True)

    valor: EmailStr


class Senha(BaseModel):
    """Senha do cliente, validada contra a politica minima.

    A politica espelha a do User Pool do Cognito (minimo de 8 caracteres).

    Atributos:
        valor: Senha em texto (transiente; nunca persistida no dominio).
    """

    model_config = ConfigDict(frozen=True)

    valor: str = Field(min_length=8)
