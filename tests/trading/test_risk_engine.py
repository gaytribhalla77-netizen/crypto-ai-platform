from backend.trading.risk_manager.engine import RiskEngine


def test_per_trade_failure_blocks_before_portfolio_check():
    engine = RiskEngine()
    decision = engine.validate(
        side="BUY", amount_usdt=999999, entry_price=100,
        balance=1000, exposure=0, daily_loss_pct=0, open_positions=0,
        automatic=True,
    )
    assert decision.allowed is False
    assert "per-trade" in decision.reason


def test_portfolio_failure_blocks_even_if_per_trade_ok():
    engine = RiskEngine()
    decision = engine.validate(
        side="BUY", amount_usdt=5, entry_price=100,
        balance=100, exposure=0, daily_loss_pct=10, open_positions=0,
        automatic=False,
    )
    assert decision.allowed is False
    assert "portfolio" in decision.reason


def test_combined_pass_returns_stop_and_take_profit():
    engine = RiskEngine()
    decision = engine.validate(
        side="BUY", amount_usdt=5, entry_price=100,
        balance=1000, exposure=0, daily_loss_pct=0, open_positions=0,
        automatic=False,
    )
    assert decision.allowed is True
    assert decision.stop_loss_price == 95
    assert decision.take_profit_price == 105
