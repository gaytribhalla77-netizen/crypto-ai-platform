"""Market-scanner worker.

Previously an empty file. Polls technical analysis for the configured
watchlist on an interval and keeps the latest reading per symbol in memory,
so other workers (e.g. opportunity_scanner) don't each have to hit the
public Binance API independently.
"""
import asyncio
import logging

from ai.technical.service import technical_analysis
from core.config import settings

logger = logging.getLogger("workers.market_scanner")


class MarketScanner:
    def __init__(self, symbols: tuple[str, ...] | None = None, interval_seconds: int = 20):
        self.symbols = symbols or settings.watchlist_symbols
        self.interval_seconds = interval_seconds
        self.latest: dict[str, dict] = {}

    async def run_once(self):
        for symbol in self.symbols:
            try:
                self.latest[symbol] = await technical_analysis(symbol)
            except Exception as e:
                logger.warning("market_scanner failed for %s: %s", symbol, e)
        return dict(self.latest)

    def get(self, symbol: str) -> dict | None:
        return self.latest.get(symbol.upper())

    async def run_forever(self):
        while True:
            await self.run_once()
            await asyncio.sleep(self.interval_seconds)


market_scanner = MarketScanner()
