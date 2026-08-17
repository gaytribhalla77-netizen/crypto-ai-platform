import httpx

BASE = "https://api.binance.com"

async def ticker(symbol: str):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BASE}/api/v3/ticker/24hr", params={"symbol": symbol.upper()})
        r.raise_for_status()
        return r.json()

async def klines(symbol: str, interval: str = "1m", limit: int = 100,
                  start_time_ms: int | None = None, end_time_ms: int | None = None):
    params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
    if start_time_ms is not None:
        params["startTime"] = start_time_ms
    if end_time_ms is not None:
        params["endTime"] = end_time_ms
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BASE}/api/v3/klines", params=params)
        r.raise_for_status()
        return r.json()


async def klines_history(symbol: str, interval: str = "15m", total: int = 3000):
    """Page backward past the single-call 1000-candle limit to build a
    larger training set. Used by ai.ml.train, not by the live app."""
    out: list = []
    end_time = None
    async with httpx.AsyncClient(timeout=15) as client:
        while len(out) < total:
            batch_limit = min(1000, total - len(out))
            params = {"symbol": symbol.upper(), "interval": interval, "limit": batch_limit}
            if end_time is not None:
                params["endTime"] = end_time
            r = await client.get(f"{BASE}/api/v3/klines", params=params)
            r.raise_for_status()
            batch = r.json()
            if not batch:
                break
            out = batch + out
            end_time = batch[0][0] - 1  # page further back in time
            if len(batch) < batch_limit:
                break
    return out[-total:]


async def depth(symbol: str, limit: int = 100):
    """Live Binance public order book. Read-only; never uses trading credentials."""
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"{BASE}/api/v3/depth", params={"symbol": symbol.upper(), "limit": limit})
        r.raise_for_status()
        data = r.json()
    bids = [(float(p), float(q)) for p, q in data.get("bids", [])]
    asks = [(float(p), float(q)) for p, q in data.get("asks", [])]
    bid_notional = sum(p*q for p,q in bids)
    ask_notional = sum(p*q for p,q in asks)
    total = bid_notional + ask_notional
    return {
        "symbol": symbol.upper(),
        "bid_notional": bid_notional,
        "ask_notional": ask_notional,
        "imbalance": (bid_notional - ask_notional) / total if total else 0.0,
        "best_bid": bids[0][0] if bids else None,
        "best_ask": asks[0][0] if asks else None,
    }
