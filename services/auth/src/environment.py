"""Configuracao tipada do servico de auth (camada Frameworks & Drivers).

Settings separados por contexto (`AuthSettings`, `AppSettings`) agregados em
`Settings`, com ponto de acesso unico e cacheado `get_settings()`. O servico
de auth NAO possui banco de dados: fala apenas com o Cognito.
"""

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_ENV_FILE = ".env"


class AuthSettings(BaseSettings):
    """Configuracao do provedor de identidade (Cognito).

    Atributos:
        aws_region: Regiao AWS do User Pool do Cognito.
        aws_endpoint_url: Endpoint AWS customizado (emuladores); vazio = AWS real.
        cognito_user_pool_id: Id do User Pool (AdminConfirmSignUp/ListUsers).
        cognito_client_id: Id do App Client (SignUp/InitiateAuth).
        cognito_issuer: Emissor esperado dos JWTs. Vazio => derivado de regiao/pool.
        jwks_url: Endereco do JWKS. Vazio => derivado de ``cognito_issuer``.
    """

    model_config = SettingsConfigDict(
        env_file=_ENV_FILE,
        extra="ignore",
    )

    aws_region: str = Field(default="us-east-1", description="Regiao AWS do Cognito.")
    aws_endpoint_url: str = Field(
        default="",
        description="Endpoint AWS customizado (ex.: emulador). Vazio => AWS real.",
    )
    cognito_user_pool_id: str = Field(description="Id do User Pool do Cognito.")
    cognito_client_id: str = Field(description="Id do App Client do Cognito.")
    cognito_issuer: str = Field(
        default="",
        description="Emissor esperado do JWT (iss). Vazio => derivado de regiao/pool.",
    )
    jwks_url: str = Field(
        default="",
        description="URL do JWKS. Vazio => derivado de cognito_issuer.",
    )

    @model_validator(mode="after")
    def _derivar_issuer_e_jwks(self) -> "AuthSettings":
        """Deriva issuer/JWKS do User Pool quando nao informados explicitamente."""
        if not self.cognito_issuer:
            self.cognito_issuer = (
                f"https://cognito-idp.{self.aws_region}.amazonaws.com/{self.cognito_user_pool_id}"
            )
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


class RateLimitSettings(BaseSettings):
    """Configuracao de rate limiting por IP (prefixo ``RATELIMIT_``).

    Os limites sao contados POR PROCESSO (slowapi em memoria); a premissa
    operacional e 1 worker uvicorn por servico. Com N workers/replicas os
    limites efetivos se diluem N vezes.

    Atributos:
        enabled: Liga/desliga o rate limiting (desligavel em testes).
        register: Limite do POST /v1/auth/register (formato slowapi).
        login: Limite do POST /v1/auth/login (formato slowapi).
        clientes: Limite dos GET /v1/clientes/* (protege a quota do Cognito).
    """

    model_config = SettingsConfigDict(
        env_prefix="RATELIMIT_",
        env_file=_ENV_FILE,
        extra="ignore",
    )

    enabled: bool = Field(default=True, description="Liga/desliga o rate limiting.")
    register: str = Field(default="5/minute", description="Limite por IP do register.")
    login: str = Field(default="10/minute", description="Limite por IP do login.")
    clientes: str = Field(default="30/minute", description="Limite por IP de /v1/clientes/*.")


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
        auth: Configuracao do provedor de identidade.
        cors: Configuracao de CORS.
        ratelimit: Configuracao de rate limiting.
        app: Configuracao geral da aplicacao.
    """

    model_config = {"frozen": True}

    auth: AuthSettings
    cors: CorsSettings
    ratelimit: RateLimitSettings
    app: AppSettings


@lru_cache
def get_settings() -> Settings:
    """Carrega e cacheia as configuracoes do servico.

    Returns:
        Instancia unica de `Settings` com todos os contextos resolvidos.
    """
    # Os campos sem default sao preenchidos pelo pydantic-settings a partir do
    # ambiente em tempo de execucao; o ty nao modela isso estaticamente.
    return Settings(
        auth=AuthSettings(),  # ty: ignore[missing-argument]
        cors=CorsSettings(),
        ratelimit=RateLimitSettings(),
        app=AppSettings(),
    )
