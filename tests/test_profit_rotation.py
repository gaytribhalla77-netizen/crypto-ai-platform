from backend.strategies.profit_rotation import RotationConfig, build_plan, manage_position


def test_profit_target_is_net_of_round_trip_costs():
    cfg = RotationConfig(target_net_pct=1.75, fee_rate=0.001, slippage_rate=0.0005)
    assert cfg.round_trip_cost_pct == 0.3
    assert cfg.gross_target_pct == 2.05


def test_position_books_profit_only_after_gross_target():
    cfg = RotationConfig()
    at_target = manage_position(100.0, 102.05, cfg)
    below_target = manage_position(100.0, 102.04, cfg)
    assert at_target.action == "TAKE_PROFIT"
    assert "rescan" in at_target.reason.lower()
    assert below_target.action == "HOLD"


def test_position_exits_at_risk_limit():
    result = manage_position(100.0, 99.10, RotationConfig())
    assert result.action == "SELL"
    assert result.strategy == "RISK_EXIT"


def test_insufficient_history_is_fail_closed():
    result = build_plan([100.0] * 29)
    assert result.action == "NO_TRADE"
    assert result.strategy == "NONE"


def test_strategy_plan_contains_competing_candidates():
    closes = [100 + i * 0.15 for i in range(50)]
    result = build_plan(closes)
    assert len(result.candidates) == 3
    assert all(candidate.name for candidate in result.candidates)
