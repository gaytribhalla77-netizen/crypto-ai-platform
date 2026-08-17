"""Health-monitor worker.

Previously an empty file — nothing populated monitoring.health.HealthRegistry,
so GET /api/v09-15/health always reported an empty, vacuously "ok" snapshot
regardless of whether the database, exchange, or AI provider were actually
reachable. This worker periodically probes each dependency and records the
result in the shared health_registry singleton.
"""
import asyncio
import os

from monitoring.health import health_registry
from database.session import SessionLocal
from exchanges.binance.client import BinanceClient
from core.config import settings
from sqlalchemy import text


class HealthMonitorWorker:
    def __init__(self, interval_seconds: int = 30):
        self.interval_seconds = interval_seconds
        self.exchange_client = BinanceClient(testnet=not settings.live_trading)

    async def check_database(self):
        try:
            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
            health_registry.set("database", "ok")
        except Exception as e:
            health_registry.set("database", "down", detail=str(e))

    async def check_exchange(self):
        try:
            await self.exchange_client.exchange_info("BTCUSDT")
            health_registry.set("binance_live" if settings.live_trading else "binance_testnet", "ok")
        except Exception as e:
            health_registry.set("binance_live" if settings.live_trading else "binance_testnet", "down", detail=str(e))

    async def check_ai_provider(self):
        # We don't spend a real API call on a health check — just confirm
        # configuration is present, and note explicitly that this does not
        # confirm the provider is actually reachable.
        if os.getenv("AI_API_KEY"):
            health_registry.set("ai_provider", "ok", detail="configured (not call-verified)")
        else:
            health_registry.set("ai_provider", "degraded", detail="AI_API_KEY not set — AI provider not configured; no synthetic provider is active")

    async def run_once(self):
        await asyncio.gather(
            self.check_database(),
            self.check_exchange(),
            self.check_ai_provider(),
        )

    async def run_forever(self):
        while True:
            await self.run_once()
            await asyncio.sleep(self.interval_seconds)
