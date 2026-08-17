import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./crypto_ai.db")
engine = create_async_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    from database.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight forward migration for installations created before the
        # live-protection column existed. This keeps the project deployable
        # without pretending create_all alters existing tables.
        if engine.url.get_backend_name() == "sqlite":
            cols = await conn.execute(text("PRAGMA table_info(positions)"))
            names = {row[1] for row in cols.fetchall()}
            if "protection_order_list_id" not in names:
                await conn.execute(text("ALTER TABLE positions ADD COLUMN protection_order_list_id VARCHAR(128)"))
        elif engine.url.get_backend_name() == "postgresql":
            await conn.execute(text("ALTER TABLE positions ADD COLUMN IF NOT EXISTS protection_order_list_id VARCHAR(128)"))
