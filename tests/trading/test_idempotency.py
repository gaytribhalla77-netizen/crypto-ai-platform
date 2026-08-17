import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from backend.database.models import Base
from backend.database.repository import TradeRepository, DuplicateTradeRequest


@pytest_asyncio.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as s:
        yield s


@pytest.mark.asyncio
async def test_duplicate_client_request_id_is_rejected(session):
    repo = TradeRepository(session)
    await repo.create_idempotent(
        user_id=1, symbol="BTCUSDT", side="BUY", amount_usdt=5,
        status="PENDING", client_request_id="req-1",
    )
    with pytest.raises(DuplicateTradeRequest):
        await repo.create_idempotent(
            user_id=1, symbol="BTCUSDT", side="BUY", amount_usdt=5,
            status="PENDING", client_request_id="req-1",
        )


@pytest.mark.asyncio
async def test_different_request_ids_both_succeed(session):
    repo = TradeRepository(session)
    t1 = await repo.create_idempotent(
        user_id=1, symbol="BTCUSDT", side="BUY", amount_usdt=5,
        status="PENDING", client_request_id="req-a",
    )
    t2 = await repo.create_idempotent(
        user_id=1, symbol="BTCUSDT", side="BUY", amount_usdt=5,
        status="PENDING", client_request_id="req-b",
    )
    assert t1.id != t2.id
