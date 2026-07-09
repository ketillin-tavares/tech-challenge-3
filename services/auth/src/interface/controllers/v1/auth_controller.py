"""Controller do contexto de Identidade/Auth (/v1/auth).

O provedor de identidade (Cognito) e injetado via `Depends` (testavel); o
caso de uso e montado aqui, na borda.
"""

from fastapi import APIRouter

from src.application.dtos.auth import (
    AutenticarClienteCommand,
    ClienteRegistradoDTO,
    RegistrarClienteCommand,
    TokensDTO,
)
from src.application.use_cases.autenticar_cliente import AutenticarCliente
from src.application.use_cases.registrar_cliente import RegistrarCliente
from src.interface.controllers.dependencies import IdentityDep

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", status_code=201, response_model=ClienteRegistradoDTO)
async def registrar(
    comando: RegistrarClienteCommand, identity: IdentityDep
) -> ClienteRegistradoDTO:
    """Registra um novo cliente (auto-confirmado no Cognito).

    Args:
        comando: Credenciais de registro (email e senha).
        identity: Provedor de identidade injetado.

    Returns:
        Identificador opaco (`sub`) do cliente registrado.
    """
    caso = RegistrarCliente(identity)
    return await caso.executar(comando)


@router.post("/login", response_model=TokensDTO)
async def login(comando: AutenticarClienteCommand, identity: IdentityDep) -> TokensDTO:
    """Autentica um cliente e retorna os tokens.

    Args:
        comando: Credenciais de login (email e senha).
        identity: Provedor de identidade injetado.

    Returns:
        Tokens emitidos pelo provedor de identidade.
    """
    caso = AutenticarCliente(identity)
    return await caso.executar(comando)
