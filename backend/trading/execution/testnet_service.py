"""DEPRECATED — duplicate of trading.testnet_service.TestnetTradeService.

This class used to exist in parallel with trading/testnet_service.py,
called a nonexistent client method (place_test_order), was never wired to
any route, and never went through the risk engine's portfolio-level check
or idempotency. Nothing imports it. Kept only as a pointer so anyone
searching for it lands on the real implementation.
"""
from trading.testnet_service import TestnetTradeService  # noqa: F401 — re-exported for discoverability
