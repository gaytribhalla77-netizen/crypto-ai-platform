from __future__ import annotations
import os
import httpx


class OandaExecution:
    """Real OANDA v20 order/position adapter. No simulation."""
    def __init__(self, token=None, account_id=None, practice=None):
        self.token = token or os.getenv("OANDA_API_TOKEN", "")
        self.account_id = account_id or os.getenv("OANDA_ACCOUNT_ID", "")
        self.practice = (os.getenv("OANDA_PRACTICE", "true").lower() == "true") if practice is None else practice
        self.base = "https://api-fxpractice.oanda.com" if self.practice else "https://api-fxtrade.oanda.com"
        self.timeout = float(os.getenv("FX_HTTP_TIMEOUT", "10"))

    @property
    def configured(self): return bool(self.token and self.account_id)

    def headers(self):
        if not self.configured: raise RuntimeError("OANDA credentials are not configured.")
        return {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}

    def instrument(self, symbol):
        s = symbol.upper().replace("/", "_").replace("-", "_")
        return s if "_" in s else f"{s[:3]}_{s[3:]}"

    async def account_summary(self):
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.get(f"{self.base}/v3/accounts/{self.account_id}/summary", headers=self.headers())
            r.raise_for_status(); return r.json()

    async def open_positions(self):
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.get(f"{self.base}/v3/accounts/{self.account_id}/openPositions", headers=self.headers())
            r.raise_for_status(); return r.json()

    async def open_trades(self):
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.get(f"{self.base}/v3/accounts/{self.account_id}/openTrades", headers=self.headers())
            r.raise_for_status(); return r.json()

    async def place_market_order(self, symbol, units, stop_loss=None, take_profit=None, client_order_id=None):
        order = {"type": "MARKET", "instrument": self.instrument(symbol), "units": str(units), "timeInForce": "FOK", "positionFill": "DEFAULT"}
        if stop_loss is not None: order["stopLossOnFill"] = {"price": str(stop_loss), "timeInForce": "GTC"}
        if take_profit is not None: order["takeProfitOnFill"] = {"price": str(take_profit), "timeInForce": "GTC"}
        if client_order_id: order["clientExtensions"] = {"id": client_order_id, "tag": "real-ai-agent"}
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.post(f"{self.base}/v3/accounts/{self.account_id}/orders", headers=self.headers(), json={"order": order})
            r.raise_for_status(); return r.json()

    async def close_position(self, symbol, long_units="ALL", short_units="ALL"):
        body = {"longUnits": str(long_units), "shortUnits": str(short_units)}
        async with httpx.AsyncClient(timeout=self.timeout) as c:
            r = await c.put(f"{self.base}/v3/accounts/{self.account_id}/positions/{self.instrument(symbol)}/close", headers=self.headers(), json=body)
            r.raise_for_status(); return r.json()
