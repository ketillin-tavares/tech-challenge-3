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

    # Verifica constraint UNIQUE em vendas
    result = await db_session.execute(
        text("""
            SELECT constraint_name
            FROM information_schema.table_constraints
            WHERE table_name = 'vendas' AND constraint_type = 'UNIQUE'
        """)
    )
    constraints = {row[0] for row in result.all()}
    assert "uq_vendas_veiculo_id" in constraints
