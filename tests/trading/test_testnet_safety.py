import pytest
from backend.trading.execution.service import ExecutionEngine
from backend.exchanges.binance.filters import validate_order_filters


def test_live_execution_engine_is_hard_blocked():
    engine = ExecutionEngine()
    with pytest.raises(RuntimeError):
        engine.execute()


def test_order_filters_reject_below_min_notional():
    ok, reason = validate_order_filters(
        quantity=0.0001, price=100, min_qty=0.0001, max_qty=100,
        step_size=0.0001, min_notional=10,
    )
    assert ok is False
    assert "notional" in reason.lower()


def test_order_filters_reject_bad_step_precision():
    ok, reason = validate_order_filters(
        quantity=0.00015, price=50000, min_qty=0.0001, max_qty=100,
        step_size=0.0001, min_notional=10,
    )
    assert ok is False


def test_order_filters_accept_valid_order():
    ok, reason = validate_order_filters(
        quantity=0.001, price=50000, min_qty=0.0001, max_qty=100,
        step_size=0.0001, min_notional=10,
    )
    assert ok is True
