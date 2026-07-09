"""Configuracao tipada da aplicacao (camada Frameworks & Drivers).

Estrategia (ver plano, secao 3):
  - Settings separados por contexto: `DatabaseSettings`, `AuthSettings`,
    `AppSettings`. Cada um le suas variaveis de ambiente de forma isolada.
  - Um agregador `Settings` da acesso a todos os contextos.
  - Ponto de acesso unico e cacheado: `get_settings() -> Settings`,
    injetado via DI na borda (sem `os.getenv` espalhado pelo codigo).

As variaveis sao lidas de variaveis de ambiente (e de um arquivo `.env` em
desenvolvimento). Veja `env.example` para o conjunto esperado.
"""

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_ENV_FILE = ".env"


class DatabaseSettings(BaseSettings):
    """Configuracao de acesso ao PostgreSQL (prefixo de ambiente ``DATABASE_``).

    Atributos:
        url: DSN async do PostgreSQL (ex.: ``postgresql+asyncpg://user:pass@host:5432/db``).
    """

    model_config = SettingsConfigDict(
        env_prefix="DATABASE_",
        env_file=_ENV_FILE,
        extra="ignore",
    )

    url: str = Field(
        description="DSN async do PostgreSQL usado pelo SQLAlchemy.",
    )


class AuthSettings(BaseSettings):
    """Configuracao da ACL de validacao de token (JWKS do Cognito).

    Este servico apenas VALIDA access tokens (iss, exp, client_id, grupos) via
    JWKS -- o registro/login de clientes vive no servico de auth, apartado.

    Atributos:
        cognito_client_id: App Client esperado (claim ``client_id`` do access token).
        cognito_issuer: Emissor esperado do JWT (claim ``iss``).
        jwks_url: Endereco do JWKS. Se omitido, derivado de ``cognito_issuer``.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        extra="ignore",
    )

    cognito_client_id: str = Field(
        description="Id do App Client do Cognito (validado no claim client_id do access token)."
    )
    cognito_issuer: str = Field(description="Emissor esperado do JWT (iss).")
    jwks_url: str = Field(
        default="",
        description="URL do JWKS. Vazio => derivado de cognito_issuer.",
    )

    @model_validator(mode="after")
    def _default_jwks_url(self) -> "AuthSettings":
        """Deriva o JWKS a partir do issuer quando nao informado explicitamente."""
        if not self.jwks_url:
            self.jwks_url = f"{self.cognito_issuer.rstrip('/')}/.well-known/jwks.json"
        return self


class AppSettings(BaseSettings):
    """Configuracao geral da aplicacao/observabilidade.

    Atributos:
        environment: Ambiente de execucao (``development``, ``staging``, ``production``).
        log_level: Nivel minimo de log estruturado.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        extra="ignore",
    )

    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Ambiente de execucao da aplicacao.",
    )
    log_level: LogLevel = Field(default="INFO", description="Nivel minimo de log.")


class Settings(BaseModel):
    """Agregador imutavel de todos os contextos de configuracao.

    Atributos:
        database: Configuracao de banco de dados.
        auth: Configuracao de identidade/autenticacao.
        app: Configuracao geral da aplicacao.
    """

    model_config = {"frozen": True}

    database: DatabaseSettings
    auth: AuthSettings
    app: AppSettings


@lru_cache
def get_settings() -> Settings:
    """Carrega e cacheia as configuracoes da aplicacao.

    Cada contexto e instanciado a partir do ambiente (e do arquivo ``.env`` em
    desenvolvimento) uma unica vez por processo, gracas ao cache.

    Returns:
        Instancia unica de `Settings` com todos os contextos resolvidos.
    """
    # Os campos sem default sao preenchidos pelo pydantic-settings a partir do
    # ambiente em tempo de execucao; o ty nao modela isso estaticamente.
    return Settings(
        database=DatabaseSettings(),  # ty: ignore[missing-argument]
        auth=AuthSettings(),  # ty: ignore[missing-argument]
        app=AppSettings(),
    )
