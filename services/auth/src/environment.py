"""Configuracao tipada do servico de auth (camada Frameworks & Drivers).

Settings separados por contexto (`AuthSettings`, `AppSettings`) agregados em
`Settings`, com ponto de acesso unico e cacheado `get_settings()`. O servico
de auth NAO possui banco de dados: fala apenas com o Cognito.
"""

from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_ENV_FILE = ".env"


class AuthSettings(BaseSettings):
    """Configuracao do provedor de identidade (Cognito).

    Atributos:
        aws_region: Regiao AWS do User Pool do Cognito.
        aws_endpoint_url: Endpoint AWS customizado (emuladores); vazio = AWS real.
        cognito_user_pool_id: Id do User Pool (AdminConfirmSignUp).
        cognito_client_id: Id do App Client (SignUp/InitiateAuth).
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
        app: Configuracao geral da aplicacao.
    """

    model_config = {"frozen": True}

    auth: AuthSettings
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
        app=AppSettings(),
    )
