"""Fixtures dos testes da API HTTP do servico de auth."""

from collections.abc import Iterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import create_app


@pytest.fixture
def app() -> FastAPI:
    """Fornece uma instancia fresca da aplicacao por teste."""
    return create_app()


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    """Fornece um TestClient sobre a aplicacao."""
    with TestClient(app) as test_client:
        yield test_client
