"""Comandos e DTOs do contexto de Identidade/Auth."""

from pydantic import BaseModel


class RegistrarClienteCommand(BaseModel):
    """Dados de entrada para registrar um cliente."""

    email: str
    senha: str
    nome: str
    cpf: str


class AutenticarClienteCommand(BaseModel):
    """Dados de entrada para autenticar um cliente."""

    email: str
    senha: str


class ClienteRegistradoDTO(BaseModel):
    """Resultado do registro. O `cpf` e o valor COMPLETO (normalizado);
    o mascaramento na resposta HTTP e decisao da borda (presenter)."""

    sub: str
    nome: str
    cpf: str


class ClienteRegistradoResponse(BaseModel):
    """Resposta HTTP do registro (CPF MASCARADO por minimizacao de PII)."""

    sub: str
    nome: str
    cpf_mascarado: str


class PerfilClienteDTO(BaseModel):
    """Perfil de um cliente lido do provedor de identidade.

    `nome`/`cpf` podem ser None para usuarios legados criados antes da coleta
    desses atributos. O `cpf` aqui e o valor COMPLETO (normalizado); o
    mascaramento por endpoint e decisao da borda (presenter).
    """

    sub: str
    email: str
    nome: str | None = None
    cpf: str | None = None


class TokensDTO(BaseModel):
    """Tokens emitidos pelo provedor de identidade apos autenticacao."""

    id_token: str
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
