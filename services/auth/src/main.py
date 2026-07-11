"""Composition root do servico de auth (Frameworks & Drivers).

Cria e configura a aplicacao FastAPI na borda: logging estruturado, router de
auth + health e traducao das excecoes de dominio em respostas HTTP (unica
camada que conhece status codes). Nao ha banco de dados neste servico.

Executar localmente:
    uv run uvicorn src.main:app --port 8000 --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from slowapi.errors import RateLimitExceeded

from src.domain.exceptions import (
    ClienteJaExisteError,
    ClienteNaoEncontradoError,
    CredenciaisInvalidasError,
    DomainError,
    TokenInvalidoError,
)
from src.environment import CorsSettings, Settings, get_settings
from src.infrastructure.logging import configure_logging, get_logger
from src.interface.controllers import auth_router, clientes_router, health_router
from src.interface.controllers.rate_limit import limiter
from src.interface.presenters.error_presenter import ErroResponse

logger = get_logger()

# O conflito de cadastro e propositalmente GENERICO (DADOS_JA_CADASTRADOS):
# um codigo especifico num endpoint publico viraria oraculo de enumeracao
# (descobrir quais emails/CPFs ja sao clientes).
_MAPA_DOMINIO: dict[type[BaseException], tuple[int, str]] = {
    CredenciaisInvalidasError: (401, "CREDENCIAIS_INVALIDAS"),
    ClienteJaExisteError: (409, "DADOS_JA_CADASTRADOS"),
    ClienteNaoEncontradoError: (404, "CLIENTE_NAO_ENCONTRADO"),
    TokenInvalidoError: (401, "TOKEN_INVALIDO"),
}
_FALLBACK_DOMINIO: tuple[int, str] = (500, "ERRO_DOMINIO")


def _envelope(status: int, code: str, detail: object) -> JSONResponse:
    """Monta a resposta de erro padronizada.

    Args:
        status: Codigo HTTP.
        code: Codigo simbolico do erro.
        detail: Detalhe (mensagem ou lista de campos invalidos).

    Returns:
        Resposta JSON com o envelope de erro.
    """
    erro = ErroResponse(status=status, code=code, detail=detail)
    return JSONResponse(status_code=status, content=erro.model_dump())


async def domain_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Traduz uma excecao de dominio no codigo HTTP correspondente.

    Conflitos de cadastro (409) sao logados com o IP de origem (NUNCA com
    email/CPF do payload): tentativas repetidas indicam enumeracao em curso.

    Args:
        request: Requisicao em curso (origem do IP logado nos conflitos).
        exc: Excecao de dominio capturada.

    Returns:
        Resposta JSON com o envelope de erro.
    """
    status, code = _MAPA_DOMINIO.get(type(exc), _FALLBACK_DOMINIO)
    if status == 409:
        ip_origem = request.client.host if request.client else "desconhecido"
        logger.bind(ip=ip_origem, path=request.url.path).warning("conflito_de_cadastro")
    return _envelope(status, code, str(exc))


async def rate_limit_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Traduz o estouro de rate limit (slowapi) em 429 no envelope padrao.

    Args:
        request: Requisicao em curso (nao utilizada).
        exc: Excecao `RateLimitExceeded` capturada.

    Returns:
        Resposta JSON 429 com o envelope de erro.
    """
    return _envelope(429, "MUITAS_REQUISICOES", "Limite de requisicoes excedido.")


async def validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Traduz uma `pydantic.ValidationError` (ex.: VO invalido) em 422.

    Args:
        request: Requisicao em curso (nao utilizada).
        exc: Excecao de validacao capturada.

    Returns:
        Resposta JSON 422 com os campos invalidos.
    """
    detalhes: list[dict[str, str]] = []
    if isinstance(exc, ValidationError):
        detalhes = [
            {"campo": ".".join(str(parte) for parte in erro["loc"]), "erro": erro["msg"]}
            for erro in exc.errors()
        ]
    return _envelope(422, "VALIDACAO", detalhes)


def _register_exception_handlers(app: FastAPI) -> None:
    """Registra os handlers de traducao de excecao -> HTTP.

    Args:
        app: Instancia FastAPI.
    """
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(RateLimitExceeded, rate_limit_error_handler)


def _register_cors(app: FastAPI, cors: CorsSettings) -> None:
    """Registra o middleware de CORS quando ha origens configuradas.

    Sem `CORS_ORIGINS` definida o middleware nao e registrado (comportamento
    identico ao anterior). Origens sao sempre explicitas; a combinacao curinga
    + credenciais e rejeitada no boot pelo `CorsSettings`.

    Args:
        app: Instancia FastAPI.
        cors: Configuracao de CORS resolvida do ambiente.
    """
    if not cors.origins_list:
        return
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors.origins_list,
        allow_credentials=cors.allow_credentials,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
    )


def create_app() -> FastAPI:
    """Monta a aplicacao FastAPI com suas configuracoes, rotas e handlers.

    Returns:
        Instancia configurada de `FastAPI`.
    """
    settings: Settings = get_settings()
    configure_logging(settings.app.log_level)

    app = FastAPI(
        title="Servico de Auth - Revenda de Veiculos",
        version="0.1.0",
    )

    limiter.enabled = settings.ratelimit.enabled
    app.state.limiter = limiter

    _register_cors(app, settings.cors)
    _register_exception_handlers(app)
    app.include_router(auth_router)
    app.include_router(clientes_router)
    app.include_router(health_router)

    logger.info("Servico de auth inicializado (environment={})", settings.app.environment)
    return app


app = create_app()
