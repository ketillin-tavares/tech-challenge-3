"""Barrel dos routers FastAPI por contexto.

Reexporta os routers nomeados para o `main.py` registrar na aplicacao.
"""

from src.interface.controllers.health_controller import router as health_router
from src.interface.controllers.v1.compras_controller import router as compras_router
from src.interface.controllers.v1.veiculos_controller import router as veiculos_router

__all__ = ["compras_router", "health_router", "veiculos_router"]
