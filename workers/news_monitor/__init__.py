"""News-monitor worker.

Previously an empty file. Polls NewsEngine.collect() for the configured
watchlist assets on an interval and deduplicates by URL, so the same story
mirrored across multiple feeds isn't treated as N independent events (per
the project's news-safety requirement). This still does not implement
source-reliability scoring, sentiment, or freshness decay — NewsEngine
itself only returns UNASSESSED impact today (see ai/news/service.py and
news/engine.py::summarize); this worker's job is scheduling and dedup only.
"""
import asyncio
import logging

from news.engine import NewsEngine
from core.config import settings

logger = logging.getLogger("workers.news_monitor")


class NewsMonitorWorker:
    def __init__(self, assets: tuple[str, ...] | None = None, interval_seconds: int = 60):
        self.assets = assets or settings.watchlist_symbols
        self.interval_seconds = interval_seconds
        self.engine = NewsEngine()
        self._seen_urls: set[str] = set()
        self.latest: dict[str, list] = {}

    async def run_once(self):
        for asset in self.assets:
            try:
                items = await self.engine.collect(asset)
            except Exception as e:
                logger.warning("news_monitor failed for %s: %s", asset, e)
                continue
            fresh = [i for i in items if i.url not in self._seen_urls]
            for i in fresh:
                self._seen_urls.add(i.url)
            if fresh:
                self.latest[asset] = fresh
        return dict(self.latest)

    async def run_forever(self):
        while True:
            await self.run_once()
            await asyncio.sleep(self.interval_seconds)
