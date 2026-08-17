import asyncio
from decimal import Decimal

import pytest

from exchanges.binance.client import BinanceClient
from exchanges.binance.safety import symbol_filters as _symbol_filters, floor_step as _floor_step, price_tick as _price_tick


def test_binance_live_client_uses_live_base():
    c = BinanceClient(api_key="k", api_secret="s", testnet=False)
    assert c.base == "https://api.binance.com"


def test_binance_oco_payload_uses_current_order_list_endpoint(monkeypatch):
    c = BinanceClient(api_key="k", api_secret="s", testnet=False)
    captured = {}
    async def fake_request(method, path, *, params=None, signed=False):
        captured.update(method=method, path=path, params=params, signed=signed)
        return {"orderListId": 123}
    monkeypatch.setattr(c, "_request", fake_request)
    result = asyncio.run(c.order_list_oco("BTCUSDT", "SELL", 0.01, 70000, 65000, list_client_order_id="x"))
    assert result["orderListId"] == 123
    assert captured["method"] == "POST"
    assert captured["path"] == "/api/v3/orderList/oco"
    assert captured["signed"] is True
    assert captured["params"]["aboveType"] == "LIMIT_MAKER"
    assert captured["params"]["belowType"] == "STOP_LOSS"


def test_symbol_filters_and_precision_helpers():
    info = {"symbols": [{"symbol": "BTCUSDT", "filters": [
        {"filterType": "LOT_SIZE", "minQty": "0.00001", "maxQty": "1000", "stepSize": "0.00001"},
        {"filterType": "PRICE_FILTER", "tickSize": "0.10"},
        {"filterType": "MIN_NOTIONAL", "minNotional": "10"},
    ]}]}
    f = _symbol_filters(info, "BTCUSDT")
    assert f["step"] == 0.00001
    assert _floor_step(0.123456, f["step"]) == 0.12345
    assert _price_tick(65000.19, 0.10) == 65000.1


def test_oco_protection_prices_have_correct_long_ordering():
    entry = 100.0
    sl = _price_tick(entry * .95, .01)
    tp = _price_tick(entry * 1.05, .01)
    assert sl < entry < tp


def test_live_client_never_defaults_to_testnet_when_explicitly_false():
    c = BinanceClient(api_key="k", api_secret="s", testnet=False)
    assert c.testnet is False
    assert c.base.endswith("api.binance.com")

def test_reconciliation_can_lookup_missing_exchange_order_by_client_id(monkeypatch):
    import asyncio
    from security import reconciliation

    class Trade:
        id = 7
        symbol = "BTCUSDT"
        exchange_order_id = None
        client_request_id = "client-123"
        status = "SUBMITTED"

    class Repo:
        def __init__(self, session): pass
        async def update_status(self, *args, **kwargs): pass

    class Session:
        def add(self, obj): pass
        async def commit(self): pass

    class Exchange:
        async def order_status(self, symbol, order_id=None, client_order_id=None):
            assert symbol == "BTCUSDT"
            assert order_id is None
            assert client_order_id == "client-123"
            return {"status": "FILLED", "executedQty": "1", "cummulativeQuoteQty": "100"}

    monkeypatch.setattr(reconciliation, "TradeRepository", Repo)
    monkeypatch.setattr(reconciliation, "OrderReconciliation", lambda **kw: kw)
    result = asyncio.run(reconciliation.reconcile_trade(Session(), Trade(), Exchange()))
    assert result["status"] == "FILLED"
    assert result["executed_qty"] == 1.0


def test_live_position_worker_does_not_compete_with_completed_oco():
    src = open("workers/position_monitor/__init__.py", encoding="utf-8").read()
    assert "live_oco_exit_reconciled" in src
    assert "oco_status_unavailable" in src
    assert "TestnetTradeService" in src  # retained only for the non-live branch
    live_branch = src.split('if settings.live_trading:', 1)[1].split('evaluation =', 1)[0]
    assert "TestnetTradeService" not in live_branch

def test_portfolio_state_uses_live_binance_when_live_mode(monkeypatch):
    from portfolio.state import PortfolioStateService
    import portfolio.state as state
    class DummySettings: live_trading = True; single_operator_mode = True
    monkeypatch.setattr(state, 'settings', DummySettings())
    monkeypatch.setattr(state, 'CredentialVault', lambda: (_ for _ in ()).throw(RuntimeError('no vault')))
    service = PortfolioStateService()
    import asyncio
    async def run():
        try:
            await service.snapshot_and_risk_state(None, 1)
        except Exception:
            pass
    asyncio.run(run())
    assert service.exchange is not None
    assert service.exchange.testnet is False


def test_health_monitor_source_is_environment_aware():
    src = open("workers/health_monitor/__init__.py", encoding="utf-8").read()
    assert "BinanceClient(testnet=not settings.live_trading)" in src
    assert "binance_live" in src
