import hashlib
import hmac
from urllib.parse import parse_qsl, urlencode

import pytest

from exchanges.binance.testnet_client import BinanceTestnetClient


def test_testnet_client_is_hard_bound_to_binance_testnet():
    assert BinanceTestnetClient.BASE == "https://testnet.binance.vision"


def test_testnet_credentials_fail_closed(monkeypatch):
    monkeypatch.delenv("BINANCE_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_API_SECRET", raising=False)
    client = BinanceTestnetClient()
    with pytest.raises(RuntimeError, match="credentials are missing"):
        client._headers()


def test_signed_request_contains_valid_hmac_signature():
    secret = "test-secret"
    client = BinanceTestnetClient(api_key="test-key", api_secret=secret)
    signed = client._signed({"symbol": "BTCUSDT", "recvWindow": 5000})
    signature = signed.pop("signature")
    query = urlencode(signed)
    expected = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    assert signature == expected
    assert dict(parse_qsl(query))["symbol"] == "BTCUSDT"
    assert "timestamp" in signed


def test_order_rejects_missing_credentials_before_network(monkeypatch):
    client = BinanceTestnetClient(api_key="", api_secret="")

    class FailIfNetwork:
        def __init__(self, *args, **kwargs):
            raise AssertionError("network must not be reached without credentials")

    monkeypatch.setattr("exchanges.binance.testnet_client.httpx.AsyncClient", FailIfNetwork)

    async def run():
        await client.order("BTCUSDT", "BUY", "0.001")

    import asyncio
    with pytest.raises(RuntimeError, match="credentials are missing"):
        asyncio.run(run())
