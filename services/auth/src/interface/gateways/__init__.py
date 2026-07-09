"""Gateways (adapters concretos) do servico de auth."""

from src.interface.gateways.cognito_identity_provider_gateway import CognitoIdentityProvider

__all__ = ["CognitoIdentityProvider"]
