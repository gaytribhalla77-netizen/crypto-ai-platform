"""Safe Binance Testnet connectivity validation.

This module deliberately performs NO order submission. It validates that the
configured credentials can authenticate against Binance Testnet and that the
requested symbol is available with usable exchange filters.
"""
from __future__ import annotations

import os
from typing import Any

from exchanges.binance.testnet_client import BinanceTestnetClient
from exchanges.binance.filters import symbol_filters


async def validate_testnet(symbol: str = "BTCUSDT") -> dict[str, Any]:
    api_key = os.getenv("BINANCE_TESTNET_API_KEY", "")
    api_secret = os.getenv("BINANCE_TESTNET_API_SECRET", "")
    if not api_key or not api_secret:
        raise RuntimeError(
            "BINANCE_TESTNET_API_KEY and BINANCE_TESTNET_API_SECRET are required; refusing to use production credentials."
        )

    client = BinanceTestnetClient(api_key=api_key, api_secret=api_secret)
    info = await client.exchange_info(symbol)
    filters = symbol_filters(info, symbol)
    account = await client.account()

    return {
        "status": "PASS",
        "environment": "binance_testnet",
        "symbol": symbol.upper(),
        "symbol_status": next(
            s.get("status") for s in info.get("symbols", []) if s.get("symbol", "").upper() == symbol.upper()
        ),
        "filters": filters,
        "account_permissions": account.get("accountType"),
    }
