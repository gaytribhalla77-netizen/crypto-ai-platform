#!/usr/bin/env python3
"""Safe Binance Spot Testnet smoke test.

Default mode is READ-ONLY: credentials are required, but no order is sent.
Use --place-order only after confirming the testnet account has disposable
funds and the symbol/quantity are appropriate for the testnet filters.
"""
import argparse
import asyncio
import os
import sys
from decimal import Decimal

# Allow running from repository root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from exchanges.binance.testnet_client import BinanceTestnetClient

async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="BTCUSDT")
    ap.add_argument("--quantity", type=Decimal, default=Decimal("0.00001"))
    ap.add_argument("--place-order", action="store_true", help="Actually place ONE testnet MARKET BUY")
    args = ap.parse_args()
    key, secret = os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET")
    if not key or not secret:
        raise SystemExit("Set BINANCE_API_KEY and BINANCE_API_SECRET locally; never paste them into chat.")
    c = BinanceTestnetClient(key, secret)
    info = await c.exchange_info(args.symbol)
    symbol = next((x for x in info.get("symbols", []) if x.get("symbol") == args.symbol.upper()), None)
    if not symbol:
        raise SystemExit(f"{args.symbol} is not available on Binance Testnet")
    account = await c.account()
    print("TESTNET ACCOUNT: OK")
    print("SYMBOL:          OK", args.symbol.upper())
    print("ORDER MODE:     ", "ONE MARKET BUY" if args.place_order else "READ-ONLY")
    if not args.place_order:
        print("Smoke test passed without sending an order.")
        return
    result = await c.order(args.symbol, "BUY", str(args.quantity), "iq200_smoke_" + str(int(__import__('time').time())))
    print("ORDER STATUS:    ", result.get("status"))
    print("ORDER ID:        ", result.get("orderId"))
    print("EXECUTED QTY:    ", result.get("executedQty"))
    print("Testnet order completed; do not reuse this command against live credentials.")

if __name__ == "__main__":
    asyncio.run(main())
