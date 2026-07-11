"""Barrel dos routers FastAPI do servico de auth."""

from src.interface.controllers.health_controller import router as health_router
from src.interface.controllers.v1.auth_controller import router as auth_router
from src.interface.controllers.v1.clientes_controller import router as clientes_router

__all__ = ["auth_router", "clientes_router", "health_router"]
