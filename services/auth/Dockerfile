# syntax=docker/dockerfile:1
# =============================================================================
# Multistage build: instala as dependencias no estagio "builder" e copia apenas
# a .venv + o codigo para a imagem final enxuta. Servico SEM banco de dados.
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

USER appuser

EXPOSE 8000

# Healthcheck nativo em Python (a venv ja esta no PATH) -> sem instalar curl.
HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3).status == 200 else 1)"]

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
