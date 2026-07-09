"""Excecao base do dominio.

O dominio nao conhece protocolos externos (HTTP). As excecoes de dominio
expressam violacoes de regra de negocio; a camada de Interface Adapters as
traduz para os codigos de resposta adequados (ex.: 404, 409).
"""


class DomainError(Exception):
    """Erro base de todas as violacoes de regra de dominio."""
