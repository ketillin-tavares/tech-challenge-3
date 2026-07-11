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


class CorsSettings(BaseSettings):
    """Configuracao de CORS (prefixo de ambiente ``CORS_``).

    Atributos:
        origins: Origens permitidas, separadas por virgula. Vazio desabilita o
            middleware (comportamento identico ao anterior a este recurso).
        allow_credentials: Se as respostas CORS permitem credenciais (cookies).
    """

    model_config = SettingsConfigDict(
        env_prefix="CORS_",
        env_file=_ENV_FILE,
        extra="ignore",
    )

    origins: str = Field(
        default="",
        description="Origens permitidas (CSV). Vazio => CORS desabilitado.",
    )
    allow_credentials: bool = Field(
        default=False,
        description="Permite credenciais (cookies) nas respostas CORS.",
    )

    @property
    def origins_list(self) -> list[str]:
        """Origens permitidas como lista (CSV com espacos normalizados)."""
        return [origem.strip() for origem in self.origins.split(",") if origem.strip()]

    @model_validator(mode="after")
    def _proibir_wildcard_com_credenciais(self) -> "CorsSettings":
        """Falha no boot ao combinar origem curinga com credenciais (inseguro)."""
        if self.allow_credentials and "*" in self.origins_list:
            raise ValueError(
                "CORS_ORIGINS='*' nao pode ser combinado com CORS_ALLOW_CREDENTIALS=true."
            )
        return self


class CompraSettings(BaseSettings):
    """Configuracao do ciclo de vida da compra (prefixo ``COMPRA_``).

    Atributos:
        reserva_ttl_minutos: Validade da reserva do veiculo (venda PENDENTE).
        expiracao_intervalo_segundos: Intervalo da varredura de reservas vencidas.
    """

    model_config = SettingsConfigDict(
        env_prefix="COMPRA_",
        env_file=_ENV_FILE,
        extra="ignore",
    )

    reserva_ttl_minutos: int = Field(
        default=30,
        gt=0,
        le=1440,
        description="Minutos ate a reserva (venda PENDENTE) expirar.",
    )
    expiracao_intervalo_segundos: int = Field(
        default=60,
        ge=10,
        le=3600,
        description="Intervalo (s) entre varreduras de reservas vencidas.",
    )


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
        cors: Configuracao de CORS.
        compra: Configuracao do ciclo de vida da compra.
        app: Configuracao geral da aplicacao.
    """

    model_config = {"frozen": True}

    database: DatabaseSettings
    auth: AuthSettings
    cors: CorsSettings
    compra: CompraSettings
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
        cors=CorsSettings(),
        compra=CompraSettings(),
        app=AppSettings(),
    )
