"""Comandos e DTOs do contexto de Identidade/Auth."""

from pydantic import BaseModel


class RegistrarClienteCommand(BaseModel):
    """Dados de entrada para registrar um cliente."""

    email: str
    senha: str


class AutenticarClienteCommand(BaseModel):
    """Dados de entrada para autenticar um cliente."""

    email: str
    senha: str


class ClienteRegistradoDTO(BaseModel):
    """Resultado do registro: identificador opaco do cliente no IdP."""

    sub: str


class TokensDTO(BaseModel):
    """Tokens emitidos pelo provedor de identidade apos autenticacao."""

    id_token: str
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
