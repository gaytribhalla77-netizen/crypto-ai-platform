import os


def test_clawtrade_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("CLAWTRADE_ENABLED", raising=False)
    # Keep this test independent of network or a running Clawtrade process.
    assert os.getenv("CLAWTRADE_ENABLED", "false").lower() == "false"


def test_clawtrade_integration_exposes_no_order_authority():
    from pathlib import Path

    routes = Path(__file__).parents[1] / "backend" / "api" / "clawtrade_routes.py"
    text = routes.read_text(encoding="utf-8")
    assert "@router.post(\"/chat\")" in text
    assert "@router.post(\"/backtest\")" in text
    assert "place_order" not in text
    assert "/orders" not in text


def test_clawtrade_client_uses_v1_api_contract():
    from pathlib import Path

    client = Path(__file__).parents[1] / "backend" / "clawtrade" / "client.py"
    text = client.read_text(encoding="utf-8")
    assert "/api/v1/system/health" in text
    assert "/api/v1/chat" in text
    assert "/api/v1/agents" in text
    assert "/api/v1/backtest" in text
