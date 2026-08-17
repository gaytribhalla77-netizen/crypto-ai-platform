"""Non-destructive production live-trading preflight.

This script never places an order. It validates the configuration gates that
must be true before a human deliberately enables live trading.
"""
import os

REQUIRED = {
    "APP_ENV": os.getenv("APP_ENV", ""),
    "BROKER": os.getenv("BROKER", ""),
    "LIVE_TRADING": os.getenv("LIVE_TRADING", ""),
    "PAPER_TRADING": os.getenv("PAPER_TRADING", ""),
    "ENABLE_WORKERS": os.getenv("ENABLE_WORKERS", ""),
    "LIVE_TRADING_CONFIRM": os.getenv("LIVE_TRADING_CONFIRM", ""),
    "JWT_SECRET_KEY": os.getenv("JWT_SECRET_KEY", ""),
    "CREDENTIAL_VAULT_KEY": os.getenv("CREDENTIAL_VAULT_KEY", ""),
}

def main():
    errors=[]
    if REQUIRED["APP_ENV"].lower() not in {"production", "prod"}:
        errors.append("APP_ENV must be production")
    if REQUIRED["BROKER"].lower() != "binance":
        errors.append("BROKER must be binance for this live-tested path")
    if REQUIRED["LIVE_TRADING"].lower() != "true":
        errors.append("LIVE_TRADING=true is required for the deliberate live test")
    if REQUIRED["PAPER_TRADING"].lower() == "true":
        errors.append("PAPER_TRADING must be false")
    if REQUIRED["ENABLE_WORKERS"].lower() != "true":
        errors.append("ENABLE_WORKERS=true is required")
    if REQUIRED["LIVE_TRADING_CONFIRM"] != "I_UNDERSTAND_LIVE_TRADING":
        errors.append("LIVE_TRADING_CONFIRM is missing")
    if len(REQUIRED["JWT_SECRET_KEY"]) < 32:
        errors.append("JWT_SECRET_KEY must be at least 32 characters")
    if REQUIRED["CREDENTIAL_VAULT_KEY"]:
        try:
            from cryptography.fernet import Fernet
            Fernet(REQUIRED["CREDENTIAL_VAULT_KEY"].encode())
        except Exception:
            errors.append("CREDENTIAL_VAULT_KEY must be a valid Fernet key")
    else:
        errors.append("CREDENTIAL_VAULT_KEY must be configured explicitly for live trading")
    if os.getenv("BINANCE_TESTNET", "false").lower() == "true":
        errors.append("BINANCE_TESTNET must be false")
    if errors:
        print("LIVE PREFLIGHT: BLOCKED")
        for e in errors: print("-", e)
        raise SystemExit(2)
    print("LIVE PREFLIGHT: READY (NO ORDER PLACED)")

if __name__ == "__main__": main()
