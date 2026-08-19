from __future__ import annotations

import os
from typing import Any

import httpx


class ClawtradeError(RuntimeError):
    pass


class ClawtradeClient:
    """Controlled, analysis-first client for a separate Clawtrade instance.

    The existing platform remains authoritative for authentication, risk,
    execution and live-trading gates. No Clawtrade order endpoint is exposed.
    """

    def __init__(self, base_url: str | None = None, timeout: float | None = None):
        self.base_url = (base_url or os.getenv("CLAWTRADE_BASE_URL", "http://127.0.0.1:9090")).rstrip("/")
        self.timeout = timeout or float(os.getenv("CLAWTRADE_TIMEOUT_SECONDS", "10"))
        self.token = os.getenv("CLAWTRADE_API_TOKEN", "")

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    async def health(self) -> dict[str, Any]:
        return await self._get("/api/v1/system/health")

    async def price(self, symbol: str, exchange: str = "binance") -> dict[str, Any]:
        return await self._get("/api/v1/price", {"symbol": symbol, "exchange": exchange})

    async def candles(self, symbol: str, timeframe: str = "1h", limit: int = 100,
                      exchange: str = "binance") -> dict[str, Any]:
        return await self._get("/api/v1/candles", {
            "symbol": symbol, "timeframe": timeframe, "limit": limit, "exchange": exchange
        })

    async def orderbook(self, symbol: str, depth: int = 20,
                        exchange: str = "binance") -> dict[str, Any]:
        return await self._get("/api/v1/orderbook", {
            "symbol": symbol, "depth": depth, "exchange": exchange
        })

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}{path}", params=params or {}, headers=self._headers()
                )
            response.raise_for_status()
            return response.json()
        except Exception as exc:
            raise ClawtradeError(f"Clawtrade request failed: {exc}") from exc
