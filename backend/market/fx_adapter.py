from __future__ import annotations
from abc import ABC, abstractmethod
import os
import httpx


class FXMarketAdapter(ABC):
    @abstractmethod
    async def quote(self, symbol: str) -> dict: ...
    @abstractmethod
    async def candles(self, symbol: str, interval: str, limit: int = 500) -> list[dict]: ...


class OandaFXAdapter(FXMarketAdapter):
    """Real OANDA v20 market-data adapter. No synthetic quotes."""
    def __init__(self, token: str | None = None, account_id: str | None = None, practice: bool | None = None):
        self.token = token or os.getenv("OANDA_API_TOKEN", "")
        self.account_id = account_id or os.getenv("OANDA_ACCOUNT_ID", "")
        self.practice = (os.getenv("OANDA_PRACTICE", "true").lower() == "true") if practice is None else practice
        self.base = "https://api-fxpractice.oanda.com" if self.practice else "https://api-fxtrade.oanda.com"
        self.timeout = float(os.getenv("FX_HTTP_TIMEOUT", "10"))

    @property
    def configured(self) -> bool:
        return bool(self.token and self.account_id)

    def _headers(self):
        if not self.configured:
            raise RuntimeError("OANDA API token/account ID are not configured.")
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def _instrument(self, symbol: str) -> str:
        s = symbol.upper().replace("/", "_").replace("-", "_")
        return s if "_" in s else f"{s[:3]}_{s[3:]}"

    def _granularity(self, interval: str) -> str:
        mapping = {"1m":"M1", "5m":"M5", "15m":"M15", "30m":"M30", "1h":"H1", "4h":"H4", "1d":"D"}
        return mapping.get(interval.lower(), interval.upper())

    async def quote(self, symbol: str) -> dict:
        instrument = self._instrument(symbol)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(
                f"{self.base}/v3/accounts/{self.account_id}/pricing",
                params={"instruments": instrument}, headers=self._headers())
            r.raise_for_status()
            item = r.json()["prices"][0]
            bid = float(item["bids"][0]["price"])
            ask = float(item["asks"][0]["price"])
            return {"symbol": symbol.upper(), "bid": bid, "ask": ask, "mid": (bid + ask) / 2, "time": item["time"], "source": "oanda_v20"}

    async def candles(self, symbol: str, interval: str, limit: int = 500) -> list[dict]:
        instrument = self._instrument(symbol)
        count = min(max(int(limit), 1), 5000)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.get(
                f"{self.base}/v3/instruments/{instrument}/candles",
                params={"granularity": self._granularity(interval), "count": count, "price": "MBA"},
                headers=self._headers())
            r.raise_for_status()
            out = []
            for c in r.json().get("candles", []):
                if not c.get("complete"):
                    continue
                mid = c.get("mid") or {}
                out.append({"time": c["time"], "open": float(mid["o"]), "high": float(mid["h"]), "low": float(mid["l"]), "close": float(mid["c"]), "volume": int(c.get("volume", 0))})
            return out

