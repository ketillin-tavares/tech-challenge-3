"""Controller do contexto de Perfil de Cliente (/v1/clientes).

Responde "quem e este cliente?" a partir do perfil que vive no Cognito:
  - GET /v1/clientes/me: o proprio cliente (CPF MASCARADO por minimizacao);
  - GET /v1/clientes/{sub}: admins (CPF completo, justificado pela
    documentacao da venda -- o servico de vendas guarda apenas o `sub`).

O token e validado localmente (JWKS); o `/me` ainda repassa o access token ao
provedor (`GetUser`), que e o autorizador do read-path (menor privilegio).
"""

from fastapi import APIRouter, Request

from src.application.dtos.auth import PerfilClienteDTO
from src.application.use_cases.obter_perfil_por_sub import ObterPerfilPorSub
from src.application.use_cases.obter_perfil_proprio import ObterPerfilProprio
from src.interface.controllers.dependencies import AdminDep, ClienteDep, IdentityDep, TokenDep
from src.interface.controllers.rate_limit import limite_clientes, limiter
from src.interface.presenters.cpf_presenter import mascarar_cpf

router = APIRouter(prefix="/v1/clientes", tags=["clientes"])


@router.get("/me", response_model=PerfilClienteDTO)
@limiter.limit(limite_clientes)
async def obter_meu_perfil(
    request: Request,
    cliente: ClienteDep,
    token: TokenDep,
    identity: IdentityDep,
) -> PerfilClienteDTO:
    """Retorna o perfil do cliente autenticado (CPF mascarado).

    Args:
        request: Requisicao em curso (exigida pelo rate limiter).
        cliente: Identidade autenticada (validacao local do JWT).
        token: Access token bruto, repassado ao provedor.
        identity: Provedor de identidade injetado.

    Returns:
        Perfil do cliente; `nome`/`cpf` podem ser None (usuarios legados).
    """
    caso = ObterPerfilProprio(identity)
    perfil = await caso.executar(token)
    cpf_mascarado = mascarar_cpf(perfil.cpf) if perfil.cpf is not None else None
    return perfil.model_copy(update={"cpf": cpf_mascarado})


@router.get("/{sub}", response_model=PerfilClienteDTO)
@limiter.limit(limite_clientes)
async def obter_perfil_de_cliente(
    request: Request,
    sub: str,
    admin: AdminDep,
    identity: IdentityDep,
) -> PerfilClienteDTO:
    """Retorna o perfil de um cliente pelo `sub` (somente admins; CPF completo).

    Args:
        request: Requisicao em curso (exigida pelo rate limiter).
        sub: Identificador opaco do cliente (mesmo valor gravado na venda).
        admin: Identidade autenticada com grupo admin.
        identity: Provedor de identidade injetado.

    Returns:
        Perfil completo do cliente (para documentacao da venda).
    """
    caso = ObterPerfilPorSub(identity)
    return await caso.executar(sub)
