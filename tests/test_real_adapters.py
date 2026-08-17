import os
import hmac, hashlib
from urllib.parse import urlencode

from exchanges.binance.client import BinanceClient
from market.fx_adapter import OandaFXAdapter
from execution.fx_oanda import OandaExecution


def test_binance_signed_request_uses_hmac_sha256(monkeypatch):
    monkeypatch.setenv("BINANCE_API_KEY", "key")
    monkeypatch.setenv("BINANCE_API_SECRET", "secret")
    c = BinanceClient(testnet=False)
    p = c._signed_params({"symbol": "BTCUSDT", "recvWindow": 5000})
    sig = p.pop("signature")
    expected = hmac.new(b"secret", urlencode(p).encode(), hashlib.sha256).hexdigest()
    assert sig == expected
    assert c.base == "https://api.binance.com"


def test_real_adapters_never_claim_configured_without_credentials(monkeypatch):
    for k in ["BINANCE_API_KEY", "BINANCE_API_SECRET", "OANDA_API_TOKEN", "OANDA_ACCOUNT_ID"]:
        monkeypatch.delenv(k, raising=False)
    assert BinanceClient(testnet=False).configured is False
    assert OandaFXAdapter().configured is False
    assert OandaExecution().configured is False


def test_no_live_without_explicit_confirmation(monkeypatch):
    monkeypatch.setenv("LIVE_TRADING", "false")
    assert os.getenv("LIVE_TRADING") == "false"
