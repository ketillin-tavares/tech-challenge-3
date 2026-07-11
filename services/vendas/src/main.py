"""Composition root do servico de vendas (Frameworks & Drivers).

Cria e configura a aplicacao FastAPI na borda: configura o logging estruturado,
registra os routers de dominio (veiculos, compras) + health e traduz as
excecoes de dominio em respostas HTTP. A traducao excecao -> HTTP e a UNICA
camada que conhece status codes. Registro/login de clientes vivem no servico
de auth, totalmente apartado.

Executar localmente:
    uv run uvicorn src.main:app --port 8001 --reload
"""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from src.domain.exceptions import (
    DomainError,
    ReservaAtivaExistenteError,
    ReservaExpiradaError,
    TokenInvalidoError,
    TransicaoVendaInvalidaError,
    VeiculoIndisponivelError,
    VeiculoNaoEncontradoError,
    VeiculoVendidoNaoEditavelError,
    VendaNaoEncontradaError,
)
from src.environment import CorsSettings, Settings, get_settings
from src.infrastructure.database import async_engine, async_session_factory
from src.infrastructure.logging import configure_logging, get_logger
from src.infrastructure.tasks import executar_loop_expiracao
from src.interface.controllers import (
    compras_router,
    health_router,
    veiculos_router,
)
from src.interface.presenters.error_presenter import ErroResponse

logger = get_logger()

_MAPA_DOMINIO: dict[type[BaseException], tuple[int, str]] = {
    VeiculoNaoEncontradoError: (404, "VEICULO_NAO_ENCONTRADO"),
    VeiculoIndisponivelError: (409, "VEICULO_INDISPONIVEL"),
    VeiculoVendidoNaoEditavelError: (409, "VEICULO_NAO_EDITAVEL"),
    VendaNaoEncontradaError: (404, "VENDA_NAO_ENCONTRADA"),
    TransicaoVendaInvalidaError: (409, "TRANSICAO_VENDA_INVALIDA"),
    ReservaExpiradaError: (409, "RESERVA_EXPIRADA"),
    ReservaAtivaExistenteError: (409, "RESERVA_ATIVA_EXISTENTE"),
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

    Args:
        request: Requisicao em curso (nao utilizada).
        exc: Excecao de dominio capturada.

    Returns:
        Resposta JSON com o envelope de erro.
    """
    status, code = _MAPA_DOMINIO.get(type(exc), _FALLBACK_DOMINIO)
    return _envelope(status, code, str(exc))


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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Gerencia o ciclo de vida da aplicacao (task de expiracao + recursos).

    No startup, dispara a varredura periodica de reservas vencidas; no
    shutdown, cancela a task de forma limpa e descarta o engine async
    (fecha o pool de conexoes).

    Args:
        app: Instancia FastAPI (nao utilizada).

    Yields:
        None.
    """
    settings: Settings = get_settings()
    task_expiracao = asyncio.create_task(
        executar_loop_expiracao(
            async_session_factory,
            settings.compra.expiracao_intervalo_segundos,
        )
    )
    yield
    task_expiracao.cancel()
    with suppress(asyncio.CancelledError):
        await task_expiracao
    await async_engine.dispose()


def create_app() -> FastAPI:
    """Monta a aplicacao FastAPI com suas configuracoes, rotas e handlers.

    Returns:
        Instancia configurada de `FastAPI`.
    """
    settings: Settings = get_settings()
    configure_logging(settings.app.log_level)

    app = FastAPI(
        title="Plataforma de Revenda de Veiculos",
        version="0.1.0",
        lifespan=lifespan,
    )

    _register_cors(app, settings.cors)
    _register_exception_handlers(app)
    app.include_router(veiculos_router)
    app.include_router(compras_router)
    app.include_router(health_router)

    logger.info("Aplicacao inicializada (environment={})", settings.app.environment)
    return app


app = create_app()
