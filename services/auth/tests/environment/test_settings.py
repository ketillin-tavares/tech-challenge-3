"""Smoke tests do carregamento das configuracoes do servico de auth."""

import pytest

from src.environment import Settings, get_settings


@pytest.mark.unit
def test_get_settings_resolve_todos_os_contextos() -> None:
    """get_settings agrega Auth e App a partir do ambiente."""
    # Arrange / Act
    settings = get_settings()

    # Assert
    assert isinstance(settings, Settings)
    assert settings.auth.cognito_client_id == "testclientid"
    assert settings.auth.cognito_user_pool_id == "us-east-1_test000"
    assert settings.app.log_level == "INFO"


@pytest.mark.unit
def test_get_settings_e_cacheado() -> None:
    """A mesma instancia e retornada em chamadas consecutivas (lru_cache)."""
    # Arrange / Act / Assert
    assert get_settings() is get_settings()
