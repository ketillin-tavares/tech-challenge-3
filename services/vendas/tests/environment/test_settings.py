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


@pytest.mark.unit
def test_cors_settings_origins_csv_parsing(monkeypatch) -> None:
    """CorsSettings parseia CSV de origins com espacos."""
    # Arrange
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://example.com")

    # Act
    from src.environment import get_settings as _get_settings

    _get_settings.cache_clear()
    settings = _get_settings()

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
        from src.environment import get_settings as _get_settings

        _get_settings.cache_clear()
        _get_settings()


@pytest.mark.unit
def test_compra_settings_ttl_valido() -> None:
    """CompraSettings ttl deve estar entre 1 e 1440 minutos."""
    # Arrange / Act
    settings = get_settings()

    # Assert
    assert 1 <= settings.compra.reserva_ttl_minutos <= 1440


@pytest.mark.unit
def test_compra_settings_ttl_fora_faixa(monkeypatch) -> None:
    """CompraSettings ttl fora da faixa levanta erro."""
    # Arrange
    monkeypatch.setenv("COMPRA_RESERVA_TTL_MINUTOS", "0")  # Fora do intervalo

    # Act / Assert
    with pytest.raises(ValueError):
        from src.environment import get_settings as _get_settings

        _get_settings.cache_clear()
        _get_settings()
