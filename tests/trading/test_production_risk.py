from backend.trading.risk_manager.production import ProductionRiskManager

def test_auto_limit():
    r = ProductionRiskManager(max_auto_usdt=10)
    assert r.validate("BUY", 11, 100, True).allowed is False

def test_buy_protection_levels():
    r = ProductionRiskManager(stop_loss_pct=5, take_profit_pct=5)
    x = r.validate("BUY", 5, 100, False)
    assert x.allowed
    assert round(x.stop_loss_price, 2) == 95
    assert round(x.take_profit_price, 2) == 105
