"""Controller do contexto de Identidade/Auth (/v1/auth).

O provedor de identidade (Cognito) e injetado via `Depends` (testavel); o
caso de uso e montado aqui, na borda. Endpoints publicos sao rate-limited
por IP (anti forca bruta/enumeracao). O CPF retorna MASCARADO no eco do
registro (minimizacao de PII).
"""

from fastapi import APIRouter, Request

from src.application.dtos.auth import (
    AutenticarClienteCommand,
    ClienteRegistradoResponse,
    RegistrarClienteCommand,
    TokensDTO,
)
from src.application.use_cases.autenticar_cliente import AutenticarCliente
from src.application.use_cases.registrar_cliente import RegistrarCliente
from src.interface.controllers.dependencies import IdentityDep
from src.interface.controllers.rate_limit import limite_login, limite_register, limiter
from src.interface.presenters.cpf_presenter import mascarar_cpf

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=ClienteRegistradoResponse)
@limiter.limit(limite_register)
async def registrar(
    request: Request,
    comando: RegistrarClienteCommand,
    identity: IdentityDep,
) -> ClienteRegistradoResponse:
    """Registra um novo cliente (auto-confirmado no Cognito).

    Args:
        request: Requisicao em curso (exigida pelo rate limiter).
        comando: Dados de registro (email, senha, nome e CPF).
        identity: Provedor de identidade injetado.

    Returns:
        Identificador opaco (`sub`), nome e CPF mascarado do cliente.
    """
    caso = RegistrarCliente(identity)
    registrado = await caso.executar(comando)
    return ClienteRegistradoResponse(
        sub=registrado.sub,
        nome=registrado.nome,
        cpf_mascarado=mascarar_cpf(registrado.cpf),
    )


@router.post("/login", response_model=TokensDTO)
@limiter.limit(limite_login)
async def login(
    request: Request,
    comando: AutenticarClienteCommand,
    identity: IdentityDep,
) -> TokensDTO:
    """Autentica um cliente e retorna os tokens.

    Args:
        request: Requisicao em curso (exigida pelo rate limiter).
        comando: Credenciais de login (email e senha).
        identity: Provedor de identidade injetado.

    Returns:
        Tokens emitidos pelo provedor de identidade.
    """
    caso = AutenticarCliente(identity)
    return await caso.executar(comando)
