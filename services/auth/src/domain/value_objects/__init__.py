"""Value Objects do dominio de auth (imutaveis e auto-validados)."""

from src.domain.value_objects.cpf import Cpf
from src.domain.value_objects.credenciais import Email, Senha
from src.domain.value_objects.identidade import ClienteAutenticado

__all__ = ["ClienteAutenticado", "Cpf", "Email", "Senha"]
