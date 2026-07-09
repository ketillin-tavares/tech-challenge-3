"""Smoke tests do bootstrap: valida o carregamento das configuracoes.

Confirma que a fundacao (pythonpath src/, fixture autouse de ambiente e o
agregador GeneralSettings) esta funcional.
"""

import pytest

from src.environment import Settings, get_settings


@pytest.mark.unit
def test_get_settings_resolve_todos_os_contextos() -> None:
    """get_settings agrega Database, Auth e App a partir do ambiente."""
    # Arrange / Act
    settings = get_settings()

    # Assert
    assert isinstance(settings, Settings)
    assert settings.database.url.startswith("postgresql+asyncpg://")
    assert settings.auth.cognito_client_id == "testclientid"
    assert settings.app.log_level == "INFO"


@pytest.mark.unit
def test_jwks_url_derivado_do_issuer_quando_ausente() -> None:
    """Sem JWKS_URL explicito, o valor e derivado do issuer do Cognito."""
    # Arrange / Act
    auth = get_settings().auth

    # Assert
    assert auth.jwks_url == f"{auth.cognito_issuer}/.well-known/jwks.json"


@pytest.mark.unit
def test_get_settings_e_cacheado() -> None:
    """A mesma instancia e retornada em chamadas consecutivas (lru_cache)."""
    # Arrange / Act / Assert
    assert get_settings() is get_settings()
