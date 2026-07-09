# Alvos do servico de auth (uv exclusivo). Recipes de uma linha, portaveis em Git Bash.

.PHONY: install format lint typecheck test test-cov run quality ci

# --- Dependencias ------------------------------------------------------------
install:
	uv sync

# --- Qualidade (dev: mutam arquivos) -----------------------------------------
format:
	uv run ruff format src/ tests/

lint:
	uv run ruff check --fix src/ tests/

typecheck:
	uv run ty check src/

# --- Testes ------------------------------------------------------------------
test:
	uv run pytest

test-cov:
	uv run pytest --cov=src --cov-report=term-missing

# --- Aplicacao ---------------------------------------------------------------
run:
	uv run uvicorn src.main:app --port 8000 --reload

# --- Agregados ---------------------------------------------------------------
# Qualidade local (auto-fix + cobertura).
quality:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/
	uv run ty check src/
	uv run pytest --cov=src --cov-report=term-missing

# Paridade com o pipeline: NAO modifica arquivos (falha se desformatado).
ci:
	uv run ruff format --check src/ tests/
	uv run ruff check src/ tests/
	uv run ty check src/
	uv run pytest --cov=src --cov-report=term-missing
