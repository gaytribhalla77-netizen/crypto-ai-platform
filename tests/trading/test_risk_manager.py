from backend.trading.risk_manager.service import RiskManager

def test_positive_amount_is_blocked_in_scaffold():
    result = RiskManager().validate("BTCUSDT", "BUY", 5)
    assert result["allowed"] is False
