from __future__ import annotations
import hashlib
import hmac
import os
import time
from decimal import Decimal
from urllib.parse import urlencode

import httpx


class BinanceClient:
    """Real Binance Spot REST adapter.

    No simulated responses. Credentials stay server-side. Live execution is
    available only when explicitly enabled by configuration and the caller
    uses the canonical risk/execution pipeline.
    """
    LIVE_BASE = "https://api.binance.com"
    TESTNET_BASE = "https://testnet.binance.vision"

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, testnet: bool = True):
        self.api_key = api_key or os.getenv("BINANCE_API_KEY", "")
        self.api_secret = api_secret or os.getenv("BINANCE_API_SECRET", "")
        self.testnet = testnet
        self.base = self.TESTNET_BASE if testnet else self.LIVE_BASE
        self.timeout = float(os.getenv("EXCHANGE_HTTP_TIMEOUT", "10"))
        self.recv_window = int(os.getenv("BINANCE_RECV_WINDOW_MS", "5000"))

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.api_secret)

    def _headers(self):
        if not self.configured:
            raise RuntimeError("Binance API credentials are not configured.")
        return {"X-MBX-APIKEY": self.api_key}

    def _signed_params(self, params: dict) -> dict:
        if not self.configured:
            raise RuntimeError("Binance API credentials are not configured.")
        p = {k: v for k, v in params.items() if v is not None}
        p.setdefault("recvWindow", self.recv_window)
        p["timestamp"] = int(time.time() * 1000)
        query = urlencode(p, doseq=True)
        p["signature"] = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        return p

    async def _request(self, method: str, path: str, *, params: dict | None = None, signed: bool = False):
        final_params = self._signed_params(params or {}) if signed else (params or {})
        headers = self._headers() if signed else {"X-MBX-APIKEY": self.api_key} if self.api_key else {}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.request(method, f"{self.base}{path}", params=final_params, headers=headers)
            response.raise_for_status()
            return response.json()

    async def server_time(self) -> dict:
        return await self._request("GET", "/api/v3/time")

    async def exchange_info(self, symbol: str | None = None) -> dict:
        return await self._request("GET", "/api/v3/exchangeInfo", params={"symbol": symbol.upper()} if symbol else {})

    async def get_account(self) -> dict:
        return await self._request("GET", "/api/v3/account", params={}, signed=True)

    async def get_ticker(self, symbol: str) -> dict:
        return await self._request("GET", "/api/v3/ticker/24hr", params={"symbol": symbol.upper()})

    async def get_price(self, symbol: str) -> dict:
        return await self._request("GET", "/api/v3/ticker/price", params={"symbol": symbol.upper()})

    async def get_order_book(self, symbol: str, limit: int = 100) -> dict:
        return await self._request("GET", "/api/v3/depth", params={"symbol": symbol.upper(), "limit": limit})

    async def get_open_orders(self, symbol: str | None = None) -> list[dict]:
        params = {"symbol": symbol.upper()} if symbol else {}
        return await self._request("GET", "/api/v3/openOrders", params=params, signed=True)

    async def get_order(self, symbol: str, order_id: str | int | None = None, client_order_id: str | None = None) -> dict:
        params = {"symbol": symbol.upper()}
        if order_id is not None:
            params["orderId"] = order_id
        elif client_order_id:
            params["origClientOrderId"] = client_order_id
        else:
            raise ValueError("order_id or client_order_id is required")
        return await self._request("GET", "/api/v3/order", params=params, signed=True)

    async def order_status(self, symbol: str, order_id: str | int | None = None, client_order_id: str | None = None) -> dict:
        return await self.get_order(symbol, order_id, client_order_id=client_order_id)

    async def place_market_order(self, symbol: str, side: str, quantity: Decimal | float, client_order_id: str | None = None) -> dict:
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": "MARKET",
            "quantity": format(Decimal(str(quantity)), "f"),
            "newOrderRespType": "FULL",
        }
        if client_order_id:
            params["newClientOrderId"] = client_order_id
        return await self._request("POST", "/api/v3/order", params=params, signed=True)

    async def order_list_oco(self, symbol: str, side: str, quantity, take_profit_price, stop_price, *, list_client_order_id: str | None = None, stop_limit_price=None) -> dict:
        """Place an exchange-side OCO protection list for an existing spot position.

        For a long spot position this is SELL: above=LIMIT_MAKER (take profit),
        below=STOP_LOSS (stop loss). Binance documents OCO as a pair where one
        order executing expires the other; this endpoint is the current order-list
        API, not the deprecated /api/v3/order/oco endpoint.
        """
        side = side.upper()
        if side not in {"BUY", "SELL"}:
            raise ValueError("OCO side must be BUY or SELL")
        q = format(Decimal(str(quantity)), "f")
        tp = format(Decimal(str(take_profit_price)), "f")
        sl = format(Decimal(str(stop_price)), "f")
        params = {
            "symbol": symbol.upper(), "side": side, "quantity": q,
            "aboveType": "LIMIT_MAKER", "abovePrice": tp,
            "belowType": "STOP_LOSS", "belowStopPrice": sl,
            "newOrderRespType": "RESULT",
        }
        if stop_limit_price is not None:
            # STOP_LOSS is deliberately used as the primary fail-safe: it is a
            # market-on-trigger order and avoids the extra failure mode of a
            # stop-limit not filling during a fast move.
            raise ValueError("stop_limit_price is unsupported for STOP_LOSS protection")
        if list_client_order_id:
            params["listClientOrderId"] = list_client_order_id
        return await self._request("POST", "/api/v3/orderList/oco", params=params, signed=True)

    async def get_order_list(self, *, order_list_id: str | int | None = None, list_client_order_id: str | None = None) -> dict:
        params = {}
        if order_list_id is not None:
            params["orderListId"] = order_list_id
        elif list_client_order_id:
            params["origClientOrderId"] = list_client_order_id
        else:
            raise ValueError("order_list_id or list_client_order_id is required")
        return await self._request("GET", "/api/v3/orderList", params=params, signed=True)

    async def cancel_order_list(self, symbol: str, *, order_list_id: str | int | None = None, list_client_order_id: str | None = None) -> dict:
        params = {"symbol": symbol.upper()}
        if order_list_id is not None:
            params["orderListId"] = order_list_id
        elif list_client_order_id:
            params["listClientOrderId"] = list_client_order_id
        else:
            raise ValueError("order_list_id or list_client_order_id is required")
        return await self._request("DELETE", "/api/v3/orderList", params=params, signed=True)

    async def cancel_order(self, symbol: str, order_id: str | int) -> dict:
        return await self._request("DELETE", "/api/v3/order", params={"symbol": symbol.upper(), "orderId": order_id}, signed=True)
