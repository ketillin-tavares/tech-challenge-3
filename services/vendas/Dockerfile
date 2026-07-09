# syntax=docker/dockerfile:1
# =============================================================================
# Multistage build (obrigatorio): compila/instala as dependencias no estagio
# "builder" e copia apenas a .venv + o codigo para a imagem final enxuta.
#
# Otimizacoes aplicadas:
#   - Cache de camadas: dependencias (pyproject/uv.lock) sao instaladas ANTES
#     de copiar o codigo-fonte, logo alterar src/ nao invalida a camada de deps.
#   - Cache de build do uv via BuildKit (--mount=type=cache) entre builds.
#   - Bytecode pre-compilado (UV_COMPILE_BYTECODE) para startup mais rapido.
#   - Imagem final sem uv, sem gerenciadores e sem pacotes apt extras: todas as
#     dependencias do projeto possuem wheels manylinux para CPython 3.13, logo
#     nenhum compilador (gcc/build-essential) e necessario.
#   - Execucao non-root (appuser) e healthcheck nativo via Python (sem curl).
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder -- resolve e instala as dependencias de producao com uv.
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# uv pinado (reproducibilidade). Atualize a tag conscientemente.
COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# So as dependencias entram nesta camada => cache reaproveitado enquanto
# pyproject.toml/uv.lock nao mudarem.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# -----------------------------------------------------------------------------
# Stage 2: Runtime -- imagem enxuta, non-root, apenas com a venv e o codigo.
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app"

# Usuario/grupo de sistema sem privilegios (DevSecOps: jamais rodar como root).
RUN groupadd --system --gid 1001 appgroup \
    && useradd --system --uid 1001 --gid appgroup --no-create-home --home-dir /app appuser

WORKDIR /app

# Artefatos ja com dono correto (chown no COPY evita uma camada extra de chmod).
COPY --from=builder --chown=appuser:appgroup /app/.venv /app/.venv
COPY --chown=appuser:appgroup src/ ./src/
# alembic.ini e necessario para o servico de migrations (alembic upgrade head).
COPY --chown=appuser:appgroup alembic.ini ./

USER appuser

EXPOSE 8001

# Healthcheck nativo em Python (a venv ja esta no PATH) -> sem instalar curl,
# reduzindo a superficie de ataque da imagem final.
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=3).status == 200 else 1)"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]
