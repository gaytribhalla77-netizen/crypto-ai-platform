from backend.exchanges.binance.testnet_client import BinanceTestnetClient


def test_testnet_client_does_not_fall_back_to_production_credentials(monkeypatch):
    monkeypatch.setenv("BINANCE_API_KEY", "production-key")
    monkeypatch.setenv("BINANCE_API_SECRET", "production-secret")
    monkeypatch.delenv("BINANCE_TESTNET_API_KEY", raising=False)
    monkeypatch.delenv("BINANCE_TESTNET_API_SECRET", raising=False)

    client = BinanceTestnetClient()
    assert client.key == ""
    assert client.secret == ""
