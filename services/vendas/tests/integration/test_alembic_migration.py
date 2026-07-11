"""Testes de integracao das migrações Alembic contra Postgres real."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.integration
async def test_database_schema_tem_tabelas_e_indices(db_session: AsyncSession) -> None:
    """Testa que as tabelas e indices esperados existem no container.

    Verifica via queries diretas ao banco que as tabelas e constraints
    estao corretamente criadas.
    """
    # Verifica tabelas
    result = await db_session.execute(
        text("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
        """)
    )
    tabelas = {row[0] for row in result.all()}
    assert "veiculos" in tabelas
    assert "vendas" in tabelas

    # Verifica indice em veiculos
    result = await db_session.execute(
        text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'veiculos'
        """)
    )
    indices = {row[0] for row in result.all()}
    assert "idx_veiculos_status_preco" in indices

    # Verifica os indices unicos PARCIAIS em vendas (migration 002 substituiu
    # a UNIQUE total: vendas CANCELADAS liberam o veiculo para recompra)
    result = await db_session.execute(
        text("""
            SELECT indexname
            FROM pg_indexes
            WHERE tablename = 'vendas'
        """)
    )
    indices_vendas = {row[0] for row in result.all()}
    assert "uq_vendas_veiculo_id_ativa" in indices_vendas
    assert "uq_vendas_cliente_pendente" in indices_vendas

    # Verifica as colunas do ciclo de vida da venda (migration 002)
    result = await db_session.execute(
        text("""
            SELECT column_name, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'vendas'
        """)
    )
    colunas = {row[0]: row[1] for row in result.all()}
    assert colunas["status"] == "NO"
    assert colunas["expira_em"] == "YES"
    assert colunas["updated_at"] == "NO"
    assert colunas["data_venda"] == "YES"
