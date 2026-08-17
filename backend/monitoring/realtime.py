from __future__ import annotations

import asyncio
import logging
from collections import defaultdict, deque
from datetime import datetime, timezone

from market.stream import BinanceMarketStream
from news.engine import NewsEngine
from ai.technical.service import technical_analysis
from news.impact import NewsImpactAnalyzer

logger = logging.getLogger("monitoring.realtime")


class RealtimeIntelligence:
    """Live, read-only market intelligence layer.

    It consumes Binance's public WebSocket bookTicker stream and refreshes
    relevant news/technical intelligence on a slower cadence. It NEVER places
    orders. Trading remains behind the normal authenticated/risk/confirmation
    routes.
    """

    def __init__(self, symbols: tuple[str, ...], news_interval: int = 60):
        self.symbols = tuple(s.upper() for s in symbols)
        self.news_interval = max(15, news_interval)
        self.stream = BinanceMarketStream(tuple(s.lower() for s in self.symbols))
        self.news = NewsEngine()
        self.impact = NewsImpactAnalyzer()
        self.latest: dict[str, dict] = {}
        self.events: deque[dict] = deque(maxlen=500)
        self.subscribers: set[asyncio.Queue] = set()
        self._last_news: dict[str, str] = {}
        self._tasks: list[asyncio.Task] = []
        self.running = False

    async def start(self):
        if self.running:
            return
        self.running = True
        self._tasks = [
            asyncio.create_task(self.stream.run(self._on_market_event)),
            asyncio.create_task(self._news_loop()),
        ]
        logger.info("Realtime intelligence started for %s", ",".join(self.symbols))

    async def stop(self):
        self.running = False
        self.stream.stop()
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()

    async def _on_market_event(self, event: dict):
        data = event.get("data", event)
        symbol = str(data.get("s", "")).upper()
        if not symbol or symbol not in self.symbols:
            return
        bid = float(data.get("b", 0) or 0)
        ask = float(data.get("a", 0) or 0)
        payload = {
            "type": "market_tick",
            "symbol": symbol,
            "bid": bid,
            "ask": ask,
            "mid": round((bid + ask) / 2, 12) if bid and ask else None,
            "spread": round(ask - bid, 12) if bid and ask else None,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        current = self.latest.setdefault(symbol, {})
        current.update(payload)
        await self._publish(payload)

    async def _news_loop(self):
        while self.running:
            for symbol in self.symbols:
                try:
                    items = await self.news.collect(symbol)
                    summary = await self.news.summarize(symbol, items)
                    technical = await technical_analysis(symbol)
                    snapshot = {
                        "type": "intelligence",
                        "symbol": symbol,
                        "news": summary,
                        "technical": technical,
                        "ts": datetime.now(timezone.utc).isoformat(),
                    }
                    self.latest.setdefault(symbol, {}).update(snapshot)
                    # Alert only on genuinely new high/critical impact news.
                    newest_key = "|".join(
                        f"{x.get('source')}|{x.get('title')}|{x.get('published_at')}"
                        for x in summary.get("items", [])[:5]
                    )
                    old_key = self._last_news.get(symbol)
                    self._last_news[symbol] = newest_key
                    if newest_key and newest_key != old_key and summary.get("market_impact", {}).get("severity") in {"HIGH", "CRITICAL"}:
                        alert = {
                            "type": "market_alert",
                            "symbol": symbol,
                            "severity": summary["market_impact"]["severity"],
                            "direction": summary["market_impact"].get("direction"),
                            "reasons": summary["market_impact"].get("reasons", []),
                            "news": summary.get("items", [])[:5],
                            "ts": datetime.now(timezone.utc).isoformat(),
                        }
                        await self._publish(alert)
                except Exception as exc:
                    logger.warning("realtime intelligence failed for %s: %s", symbol, exc)
            await asyncio.sleep(self.news_interval)

    async def _publish(self, event: dict):
        self.events.append(event)
        dead = []
        for q in self.subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                # Drop the oldest queued tick rather than blocking market ingestion.
                try:
                    q.get_nowait()
                    q.put_nowait(event)
                except Exception:
                    dead.append(q)
        for q in dead:
            self.subscribers.discard(q)

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self.subscribers.discard(q)

    def snapshot(self) -> dict:
        return {
            "running": self.running,
            "symbols": list(self.symbols),
            "latest": self.latest,
            "recent_events": list(self.events)[-50:],
        }
