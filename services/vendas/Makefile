# Alvos do projeto (uv exclusivo). Recipes de uma linha, portaveis em Git Bash.

.PHONY: install format lint typecheck test test-cov test-integration \
        run migrate pre-commit quality ci

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
# Unitarios (exclui integracao/E2E que exigem Docker).
test:
	uv run pytest -m "not integration"

test-cov:
	uv run pytest --cov=src --cov-report=term-missing -m "not integration"

# Integracao + E2E (Testcontainers; exige Docker). Sem cobertura combinada.
test-integration:
	uv run pytest -m integration --no-cov

# --- Aplicacao / banco -------------------------------------------------------
run:
	uv run uvicorn src.main:app --reload

migrate:
	uv run alembic upgrade head

# --- Agregados ---------------------------------------------------------------
pre-commit:
	uv run pre-commit run --all-files

# Qualidade local (auto-fix + cobertura).
quality:
	uv run ruff format src/ tests/
	uv run ruff check --fix src/ tests/
	uv run ty check src/
	uv run pytest --cov=src --cov-report=term-missing -m "not integration"

# Paridade com o pipeline: NAO modifica arquivos (falha se desformatado).
ci:
	uv run ruff format --check src/ tests/
	uv run ruff check src/ tests/
	uv run ty check src/
	uv run pytest --cov=src --cov-report=term-missing -m "not integration"
