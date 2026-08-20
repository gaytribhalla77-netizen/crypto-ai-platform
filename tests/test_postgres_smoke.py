import os
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine


@pytest.mark.asyncio
async def test_postgres_connection_and_schema_bootstrap():
    url = os.getenv('INTEGRATION_DATABASE_URL')
    if not url:
        pytest.skip('INTEGRATION_DATABASE_URL is not configured')

    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            await conn.execute(text('SELECT 1'))
    finally:
        await engine.dispose()
