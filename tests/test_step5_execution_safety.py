import asyncio
from decimal import Decimal

import pytest

from exchanges.binance.client import BinanceClient
from exchanges.binance.safety import floor_step, price_tick, symbol_filters
from exchanges.binance.testnet_client import BinanceTestnetClient
from execution.fx_oanda import OandaExecution


def test_binance_live_adapter_defaults_to_testnet():
    c = BinanceClient(api_key="k", api_secret="s")
    assert c.testnet is True
    assert c.base == c.TESTNET_BASE


def test_binance_missing_credentials_fail_closed():
    c = BinanceTestnetClient(api_key="", api_secret="")
    with pytest.raises(RuntimeError, match="credentials"):
        c._headers()


def test_binance_signed_params_are_deterministically_hmac_signed():
    c = BinanceTestnetClient(api_key="k", api_secret="secret")
    signed = c._signed({"symbol": "BTCUSDT", "recvWindow": 5000})
    assert signed["symbol"] == "BTCUSDT"
    assert len(signed["signature"]) == 64
    assert signed["timestamp"] > 0


def test_binance_filters_and_rounding_are_safe():
    info = {"symbols": [{"symbol": "BTCUSDT", "filters": [
        {"filterType": "LOT_SIZE", "minQty": "0.001", "maxQty": "100", "stepSize": "0.001"},
        {"filterType": "PRICE_FILTER", "tickSize": "0.10"},
        {"filterType": "MIN_NOTIONAL", "minNotional": "10"},
    ]}]}
    f = symbol_filters(info, "BTCUSDT")
    assert floor_step(1.2349, f["step"]) == 1.234
    assert price_tick(123.456, f["tick"]) == 123.4
    assert price_tick(123.401, f["tick"], up=True) == 123.5


def test_oanda_defaults_to_practice_and_rejects_missing_credentials():
    c = OandaExecution(token="", account_id="")
    assert c.practice is True
    assert c.base == "https://api-fxpractice.oanda.com"
    with pytest.raises(RuntimeError, match="credentials"):
        c.headers()


def test_oanda_instrument_normalization():
    c = OandaExecution(token="k", account_id="a")
    assert c.instrument("EUR/USD") == "EUR_USD"
    assert c.instrument("BTCUSD") == "BTC_USD"


def test_testnet_adapter_has_no_live_endpoint():
    c = BinanceTestnetClient(api_key="k", api_secret="s")
    assert c.BASE == "https://testnet.binance.vision"
    assert "api.binance.com" not in c.BASE


def test_execution_adapters_are_async_callables():
    assert asyncio.iscoroutinefunction(BinanceTestnetClient.exchange_info)
    assert asyncio.iscoroutinefunction(BinanceTestnetClient.order)
    assert asyncio.iscoroutinefunction(OandaExecution.place_market_order)
