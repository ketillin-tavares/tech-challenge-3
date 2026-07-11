"""Politica de acesso a uma venda (compartilhada pelos casos de uso de compra)."""

from src.application.dtos import TransicaoCompraCommand
from src.domain.entities import Venda
from src.domain.exceptions import VendaNaoEncontradaError


def verificar_acesso_venda(venda: Venda | None, comando: TransicaoCompraCommand) -> Venda:
    """Garante que a venda existe e pertence ao solicitante (ou e admin).

    Venda inexistente e venda de outro cliente produzem o MESMO erro
    (`VendaNaoEncontradaError` -> 404), para nao revelar a existencia de
    vendas alheias (anti-enumeracao de identificadores).

    Args:
        venda: Venda carregada do repositorio (ou None).
        comando: Comando com `venda_id`, `cliente_id` (sub do JWT) e `eh_admin`.

    Returns:
        A propria venda, quando o acesso e permitido.

    Raises:
        VendaNaoEncontradaError: Se a venda nao existe ou pertence a outro
            cliente e o solicitante nao e admin.
    """
    if venda is None:
        raise VendaNaoEncontradaError(comando.venda_id)
    if venda.cliente_id != comando.cliente_id and not comando.eh_admin:
        raise VendaNaoEncontradaError(comando.venda_id)
    return venda
