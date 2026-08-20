import os
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_postgres_connection_and_schema_bootstrap():
    url = os.getenv('INTEGRATION_DATABASE_URL')
    if not url:
        pytest.skip('INTEGRATION_DATABASE_URL is not configured')

    from backend.database.models import Base

    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
            await conn.run_sync(Base.metadata.create_all)
            result = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
            tables = {row[0] for row in result.fetchall()}
            assert 'users' in tables
            assert 'trades' in tables
    finally:
        await engine.dispose()
