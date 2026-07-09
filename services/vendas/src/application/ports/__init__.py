"""Ports da camada de aplicacao do servico de vendas.

Inclui o read-model (`VeiculoQueryService`) e o verificador de token
(`TokenVerifier`). Sao implementados por adapters concretos; as camadas
internas dependem apenas destas abstracoes.
"""

from src.application.ports.token_verifier import TokenVerifier
from src.application.ports.veiculo_query_service import VeiculoQueryService

__all__ = ["TokenVerifier", "VeiculoQueryService"]
