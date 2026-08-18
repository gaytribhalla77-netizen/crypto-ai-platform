import os, hmac, hashlib, time
from urllib.parse import urlencode
import httpx

class BinanceTestnetClient:
    BASE = "https://testnet.binance.vision"

    def __init__(self, api_key: str | None = None, api_secret: str | None = None):
        self.key = api_key or os.getenv("BINANCE_API_KEY", "")
        self.secret = api_secret or os.getenv("BINANCE_API_SECRET", "")

    def _require_credentials(self):
        if not self.key or not self.secret:
            raise RuntimeError("Binance testnet credentials are missing.")

    def _signed(self, params):
        self._require_credentials()
        p = dict(params)
        p["timestamp"] = int(time.time() * 1000)
        q = urlencode(p)
        p["signature"] = hmac.new(self.secret.encode(), q.encode(), hashlib.sha256).hexdigest()
        return p

    def _headers(self):
        self._require_credentials()
        return {"X-MBX-APIKEY": self.key}

    async def exchange_info(self, symbol=None):
        params = {"symbol": symbol.upper()} if symbol else {}
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{self.BASE}/api/v3/exchangeInfo", params=params)
            r.raise_for_status()
            return r.json()

    async def account(self):
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{self.BASE}/api/v3/account", params=self._signed({"recvWindow": 5000}), headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def order(self, symbol, side, quantity, client_order_id=None):
        params = {"symbol": symbol.upper(), "side": side.upper(), "type": "MARKET", "quantity": quantity, "recvWindow": 5000}
        if client_order_id:
            params["newClientOrderId"] = client_order_id
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{self.BASE}/api/v3/order", params=self._signed(params), headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def order_status(self, symbol, order_id):
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{self.BASE}/api/v3/order", params=self._signed({"symbol": symbol.upper(), "orderId": order_id, "recvWindow": 5000}), headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def order_list_oco(self, symbol, side, quantity, take_profit_price, stop_price, list_client_order_id=None):
        params = {
            "symbol": symbol.upper(), "side": side.upper(), "quantity": quantity,
            "aboveType": "LIMIT_MAKER", "abovePrice": take_profit_price,
            "belowType": "STOP_LOSS", "belowStopPrice": stop_price,
            "newOrderRespType": "RESULT",
        }
        if list_client_order_id:
            params["listClientOrderId"] = list_client_order_id
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.post(f"{self.BASE}/api/v3/orderList/oco", params=self._signed(params), headers=self._headers())
            r.raise_for_status()
            return r.json()

    async def cancel_order_list(self, symbol, order_list_id=None, list_client_order_id=None):
        params = {"symbol": symbol.upper()}
        if order_list_id is not None:
            params["orderListId"] = order_list_id
        elif list_client_order_id:
            params["listClientOrderId"] = list_client_order_id
        else:
            raise ValueError("order_list_id or list_client_order_id is required")
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.delete(f"{self.BASE}/api/v3/orderList", params=self._signed(params), headers=self._headers())
            r.raise_for_status()
            return r.json()
