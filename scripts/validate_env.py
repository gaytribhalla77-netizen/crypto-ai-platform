from __future__ import annotations

import os
import sys


BOOLS = {"true", "false"}


def fail(message: str) -> None:
    print(f"ERROR: {message}")
    raise SystemExit(1)


def main() -> None:
    env = os.getenv("APP_ENV", "development").lower()
    live = os.getenv("LIVE_TRADING", "false").lower()
    paper = os.getenv("PAPER_TRADING", "false").lower()

    for name, value in (("LIVE_TRADING", live), ("PAPER_TRADING", paper), ("ENABLE_WORKERS", os.getenv("ENABLE_WORKERS", "false").lower())):
        if value not in BOOLS:
            fail(f"{name} must be true or false")

    if live == "true":
        if os.getenv("LIVE_TRADING_CONFIRM") != "I_UNDERSTAND_LIVE_TRADING":
            fail("LIVE_TRADING requires the explicit confirmation gate")
        if os.getenv("ENABLE_WORKERS", "false").lower() != "true":
            fail("LIVE_TRADING requires ENABLE_WORKERS=true")
        if os.getenv("BROKER", "").lower() not in {"binance", "oanda"}:
            fail("LIVE_TRADING requires BROKER=binance or BROKER=oanda")

    secret = os.getenv("JWT_SECRET_KEY", "")
    if env in {"production", "prod"} and (not secret or secret == "dev-only-insecure-secret-change-me" or len(secret) < 32):
        fail("production requires a JWT_SECRET_KEY of at least 32 characters")

    if paper == "true" and live == "true":
        print("WARNING: both paper and live trading flags are true; live gates still take precedence")

    print(f"Environment validation passed: APP_ENV={env}, LIVE_TRADING={live}, PAPER_TRADING={paper}")


if __name__ == "__main__":
    main()
