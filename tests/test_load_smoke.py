import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app


@pytest.mark.asyncio
async def test_concurrent_health_smoke():
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        responses = await asyncio.gather(*(client.get("/health") for _ in range(100)))

    assert len(responses) == 100
    assert all(response.status_code == 200 for response in responses)
    assert all(response.json()["fail_closed"] is True for response in responses)
