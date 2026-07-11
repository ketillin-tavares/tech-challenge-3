"""Varredura periodica de reservas vencidas (task asyncio do lifespan).

Complementa a expiracao lazy do `EfetivarCompra` sem infraestrutura nova
(sem Celery/cron/fila): um loop asyncio cancela vendas PENDENTE vencidas e
devolve os veiculos a DISPONIVEL. Cada iteracao e blindada por try/except --
uma falha transitoria (ex.: banco indisponivel) e logada e a varredura
continua na proxima rodada; apenas o cancelamento da task (shutdown) escapa.
"""

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.application.use_cases.expirar_reservas_vencidas import ExpirarReservasVencidas
from src.infrastructure.logging import get_logger
from src.interface.gateways.unit_of_work_gateway import UnitOfWorkGateway

logger = get_logger()


async def _executar_varredura(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Executa uma varredura unica de reservas vencidas.

    Args:
        session_factory: Fabrica de sessoes async do banco.
    """
    caso = ExpirarReservasVencidas(UnitOfWorkGateway(session_factory))
    recibos = await caso.executar()
    if recibos:
        logger.bind(quantidade=len(recibos)).info("reservas_expiradas_canceladas")


async def executar_loop_expiracao(
    session_factory: async_sessionmaker[AsyncSession],
    intervalo_segundos: int,
) -> None:
    """Roda a varredura de reservas vencidas em loop ate ser cancelada.

    Excecoes de uma iteracao NUNCA derrubam o loop (a task morreria em
    silencio e o estoque ficaria preso em RESERVADO); somente o
    `asyncio.CancelledError` do shutdown encerra a execucao.

    Args:
        session_factory: Fabrica de sessoes async do banco.
        intervalo_segundos: Pausa entre varreduras consecutivas.
    """
    logger.bind(intervalo_segundos=intervalo_segundos).info("loop_expiracao_iniciado")
    while True:
        try:
            await _executar_varredura(session_factory)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("falha_na_varredura_de_reservas")
        await asyncio.sleep(intervalo_segundos)
