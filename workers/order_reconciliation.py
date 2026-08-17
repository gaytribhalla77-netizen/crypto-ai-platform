import asyncio
import logging
from sqlalchemy import select
from database.session import SessionLocal
from database.models import Trade
from security.reconciliation import reconcile_trade
from security.vault import CredentialVault
from core.config import settings
from exchanges.binance.client import BinanceClient

logger = logging.getLogger("workers.order_reconciliation")

class OrderReconciliationWorker:
    def __init__(self, interval=15): self.interval=interval; self.running=True

    async def tick(self):
        async with SessionLocal() as session:
            rows=(await session.execute(select(Trade).where(Trade.status.in_(["UNKNOWN","SUBMITTED","PARTIALLY_FILLED"])))) .scalars().all()
            for trade in rows:
                try:
                    creds = await CredentialVault().get_provider_credentials(session, trade.user_id, "binance")
                    client = BinanceClient(creds.get("api_key"), creds.get("api_secret"), testnet=not settings.live_trading)
                except RuntimeError:
                    if not settings.single_operator_mode: continue
                    client = BinanceClient(testnet=not settings.live_trading)
                try:
                    await reconcile_trade(session, trade, client)
                except Exception:
                    logger.exception("reconciliation failed for trade %s", trade.id)

    async def run_forever(self):
        while self.running:
            await self.tick(); await asyncio.sleep(self.interval)
