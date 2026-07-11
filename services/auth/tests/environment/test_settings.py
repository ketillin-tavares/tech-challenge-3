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


@pytest.mark.unit
def test_jwks_url_derivado_do_issuer_quando_ausente() -> None:
    """JWKS URL e derivada de issuer se nao fornecida."""
    # Arrange / Act
    settings = get_settings()

    # Assert
    assert settings.auth.jwks_url is not None
    assert "/.well-known/jwks.json" in settings.auth.jwks_url


@pytest.mark.unit
def test_cors_settings_origins_csv_parsing(monkeypatch) -> None:
    """CorsSettings parseia CSV de origins com espacos."""
    # Arrange
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://example.com")

    # Act
    settings = get_settings()

    # Assert
    assert len(settings.cors.origins_list) == 2
    assert "http://localhost:3000" in settings.cors.origins_list
    assert "https://example.com" in settings.cors.origins_list


@pytest.mark.unit
def test_cors_settings_wildcard_com_credentials_erro(monkeypatch) -> None:
    """Wildcard com allow_credentials True levanta ValueError."""
    # Arrange
    monkeypatch.setenv("CORS_ORIGINS", "*")
    monkeypatch.setenv("CORS_ALLOW_CREDENTIALS", "true")

    # Act / Assert
    with pytest.raises(ValueError):
        # Força recarregar as settings
        from src.environment import get_settings as _get_settings

        _get_settings.cache_clear()
        _get_settings()


@pytest.mark.unit
def test_cors_settings_origins_vazio_retorna_lista_vazia(monkeypatch) -> None:
    """CORS_ORIGINS vazio retorna lista vazia."""
    # Arrange
    monkeypatch.setenv("CORS_ORIGINS", "")

    # Act
    from src.environment import get_settings as _get_settings

    _get_settings.cache_clear()
    settings = _get_settings()

    # Assert
    assert settings.cors.origins_list == []


@pytest.mark.unit
def test_ratelimit_settings_defaults() -> None:
    """RateLimitSettings tem defaults validos."""
    # Arrange / Act
    settings = get_settings()

    # Assert
    assert settings.ratelimit.enabled is True
    assert settings.ratelimit.register == "5/minute"
    assert settings.ratelimit.login == "10/minute"
