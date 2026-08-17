import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from news.models import NewsItem
from news.impact import NewsImpactAnalyzer

# Free, no-key-required public RSS/Atom feeds. These are real, independent
# crypto news sources -- not "all world news", but a genuine live feed.
# Override/extend with NEWS_FEEDS=url1,url2 in .env.
DEFAULT_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://cryptoslate.com/feed/",
    "https://www.newsbtc.com/feed/",
    "https://www.theblock.co/rss.xml",
    "https://bitcoinmagazine.com/.rss/full/",
    "https://www.reddit.com/r/CryptoCurrency/.rss",
    # Official macro/regulatory feeds for market-moving events.
    "https://www.federalreserve.gov/feeds/press_all.xml",
    "https://www.sec.gov/news/pressreleases.rss",
]

# Asset name -> keywords used to match a headline to a coin.
ASSET_KEYWORDS = {
    "BTCUSDT": ["bitcoin", "btc"],
    "ETHUSDT": ["ethereum", "eth", "ether"],
    "BNBUSDT": ["bnb", "binance coin"],
    "SOLUSDT": ["solana", "sol"],
    "DOGEUSDT": ["dogecoin", "doge"],
    "XRPUSDT": ["ripple", "xrp"],
    "ADAUSDT": ["cardano", "ada"],
    "MATICUSDT": ["polygon", "matic"],
    "AVAXUSDT": ["avalanche", "avax"],
    "DOTUSDT": ["polkadot", "dot"],
    "LTCUSDT": ["litecoin", "ltc"],
    "TRXUSDT": ["tron", "trx"],
    "LINKUSDT": ["chainlink", "link"],
    "SHIBUSDT": ["shiba inu", "shib"],
}

# Deliberately simple, transparent, and auditable -- a word-count sentiment
# score, NOT an AI model. It exists so the app can surface *some* signal
# without needing an AI_API_KEY.
POSITIVE_WORDS = [
    "surge", "rally", "soar", "gain", "gains", "bullish", "breakout", "record high",
    "all-time high", "adoption", "approve", "approved", "approval", "partnership",
    "upgrade", "inflow", "inflows", "buy", "buying", "recover", "recovery", "jump",
    "climb", "outperform", "positive", "boost", "growth", "milestone",
]
NEGATIVE_WORDS = [
    "crash", "plunge", "dump", "bearish", "selloff", "sell-off", "hack", "hacked",
    "exploit", "lawsuit", "ban", "banned", "regulation crackdown", "outflow",
    "outflows", "liquidation", "liquidated", "collapse", "fraud", "scam",
    "investigation", "fine", "fined", "delist", "delisted", "warning", "decline",
    "drop", "plummet", "fear", "panic", "downturn",
]


MARKET_WIDE_KEYWORDS = [
    "federal reserve", "fed", "fomc", "interest rate", "rate decision", "inflation",
    "cpi", "ppi", "payroll", "jobs report", "nonfarm", "sec", "regulation",
    "crypto regulation", "bitcoin etf", "spot etf", "treasury", "sanctions",
    "war", "invasion", "oil", "tariff", "liquidity", "bank failure", "banking crisis",
]


def _score_sentiment(text: str) -> int:
    t = text.lower()
    score = 0
    for w in POSITIVE_WORDS:
        if w in t:
            score += 1
    for w in NEGATIVE_WORDS:
        if w in t:
            score -= 1
    return score


def _parse_rss(xml_text: str, source: str):
    items = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    for item in root.iter():
        tag = item.tag.split("}")[-1]
        if tag not in ("item", "entry"):
            continue
        title, link, pub = "", "", None
        for child in item:
            ctag = child.tag.split("}")[-1]
            if ctag == "title":
                title = (child.text or "").strip()
            elif ctag == "link":
                link = (child.text or child.get("href") or "").strip()
            elif ctag in ("pubDate", "published", "updated"):
                raw = (child.text or "").strip()
                try:
                    pub = parsedate_to_datetime(raw)
                except Exception:
                    pub = None
        if title:
            items.append({
                "title": title, "url": link, "source": source,
                "published_at": pub or datetime.now(timezone.utc),
            })
    return items


class NewsEngine:
    """Pulls real headlines from public crypto RSS/Atom feeds (no API key
    needed), filters them by asset, and scores sentiment with a transparent
    keyword count. This is intentionally simple: it is NOT an AI model and
    should not be presented to the user as one -- see ai/news/service.py
    (and ai/providers/openai_provider.py, gated on AI_API_KEY) for the
    optional real-AI path.
    """

    def __init__(self):
        self.impact_analyzer = NewsImpactAnalyzer()
        configured = [x.strip() for x in os.getenv("NEWS_FEEDS", "").split(",") if x.strip()]
        self.feeds = configured or DEFAULT_FEEDS

    async def collect(self, asset: str):
        symbol = asset.upper()
        keywords = ASSET_KEYWORDS.get(symbol, [symbol.replace("USDT", "").lower()])
        items = []
        async with httpx.AsyncClient(timeout=8, follow_redirects=True,
                                      headers={"User-Agent": "Mozilla/5.0"}) as client:
            for url in self.feeds:
                try:
                    r = await client.get(url)
                    r.raise_for_status()
                    for raw in _parse_rss(r.text, url):
                        title_l = raw["title"].lower()
                        if any(k in title_l for k in keywords) or any(k in title_l for k in MARKET_WIDE_KEYWORDS):
                            items.append(NewsItem(
                                source=raw["source"],
                                title=raw["title"],
                                url=raw["url"],
                                published_at=raw["published_at"],
                                asset=symbol,
                                confidence=0,
                            ))
                except Exception:
                    continue
        items.sort(key=lambda x: x.published_at, reverse=True)
        return items[:20]

    async def collect_bulk(self, assets: list[str]):
        """Fetch every feed once and bucket matching headlines per asset.
        Used by the watchlist dashboard so N coins don't mean N x re-fetching
        the same RSS feeds."""
        symbols = [a.upper() for a in assets]
        keyword_map = {
            s: ASSET_KEYWORDS.get(s, [s.replace("USDT", "").lower()]) for s in symbols
        }
        buckets: dict[str, list[NewsItem]] = {s: [] for s in symbols}
        async with httpx.AsyncClient(timeout=8, follow_redirects=True,
                                      headers={"User-Agent": "Mozilla/5.0"}) as client:
            for url in self.feeds:
                try:
                    r = await client.get(url)
                    r.raise_for_status()
                    parsed = _parse_rss(r.text, url)
                except Exception:
                    continue
                for raw in parsed:
                    title_l = raw["title"].lower()
                    for s in symbols:
                        if any(k in title_l for k in keyword_map[s]) or any(k in title_l for k in MARKET_WIDE_KEYWORDS):
                            buckets[s].append(NewsItem(
                                source=raw["source"], title=raw["title"], url=raw["url"],
                                published_at=raw["published_at"], asset=s, confidence=0,
                            ))
        for s in symbols:
            buckets[s].sort(key=lambda x: x.published_at, reverse=True)
            buckets[s] = buckets[s][:20]
        return buckets

    async def summarize(self, asset, items):
        if not items:
            return {
                "asset": asset.upper(),
                "count": 0,
                "sentiment_score": 0,
                "sentiment": "NO_DATA",
                "impact": "UNKNOWN",
                "confidence": 0,
                "note": "No matching headlines found in the current feeds right now.",
                "items": [],
            }
        total = 0
        scored_items = []
        for x in items:
            s = _score_sentiment(x.title)
            total += s
            scored_items.append({
                "title": x.title, "url": x.url, "source": x.source, "score": s,
                "published_at": x.published_at.isoformat() if x.published_at else None,
            })
        avg = total / len(items)
        if avg > 0.4:
            label, impact = "BULLISH", "POSITIVE"
        elif avg < -0.4:
            label, impact = "BEARISH", "NEGATIVE"
        else:
            label, impact = "MIXED", "NEUTRAL"
        impact_analysis = self.impact_analyzer.analyze(scored_items)
        return {
            "asset": asset.upper(),
            "count": len(items),
            "sentiment_score": round(avg, 2),
            "sentiment": label,
            "impact": impact,
            "confidence": min(100, len(items) * 10),
            "method": "keyword-count + recency/market-impact analysis (not AI)",
            "market_impact": impact_analysis,
            "items": scored_items,
        }
