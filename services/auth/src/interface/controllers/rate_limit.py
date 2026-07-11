"""Rate limiting por IP (slowapi) -- detalhe de framework, restrito a borda.

Mitiga forca bruta/enumeracao nos endpoints publicos (register/login) e
protege a quota das APIs do Cognito nos endpoints de perfil. Os contadores
vivem em memoria POR PROCESSO (premissa operacional: 1 worker uvicorn).

O `limiter` e configurado (enabled) no `create_app`; os limites vem das
settings em tempo de requisicao (funcoes abaixo), permitindo override por
variavel de ambiente sem reimportar os controllers.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.environment import get_settings

limiter = Limiter(key_func=get_remote_address)


def limite_register() -> str:
    """Retorna o limite por IP do endpoint de registro."""
    return get_settings().ratelimit.register


def limite_login() -> str:
    """Retorna o limite por IP do endpoint de login."""
    return get_settings().ratelimit.login


def limite_clientes() -> str:
    """Retorna o limite por IP dos endpoints de perfil de cliente."""
    return get_settings().ratelimit.clientes
