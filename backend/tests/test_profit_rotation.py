from strategies.profit_rotation import RotationConfig, build_plan, manage_position


def test_target_is_net_and_cost_adjusted():
    cfg = RotationConfig(target_net_pct=1.75, fee_rate=0.001, slippage_rate=0.0005)
    assert cfg.gross_target_pct > 1.75


def test_profit_target_emits_take_profit():
    cfg = RotationConfig(target_net_pct=1.75, fee_rate=0.0, slippage_rate=0.0)
    plan = manage_position(100.0, 101.8, cfg)
    assert plan.action == 'TAKE_PROFIT'


def test_stop_emits_risk_exit():
    cfg = RotationConfig(target_net_pct=1.75, max_loss_pct=0.9, fee_rate=0.0, slippage_rate=0.0)
    plan = manage_position(100.0, 99.0, cfg)
    assert plan.action == 'SELL'


def test_insufficient_history_refuses_trade():
    plan = build_plan([100 + i * 0.1 for i in range(10)])
    assert plan.action == 'NO_TRADE'
