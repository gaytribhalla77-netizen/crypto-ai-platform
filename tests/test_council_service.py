import asyncio

from intelligence.council_service import build_council


def test_council_service_uses_real_inputs(monkeypatch):
    async def technical(symbol):
        return {"symbol": symbol, "price": 100, "trend": "Bullish", "closes": list(range(1, 101))}
    async def collect(symbol):
        return []
    async def predict(symbol):
        return {"symbol": symbol, "status": "NOT_TRAINED"}
    async def depth(symbol, limit=100):
        return {"symbol": symbol, "bid_notional": 100, "ask_notional": 50, "imbalance": 1/3}
    monkeypatch.setattr("intelligence.council_service.technical_analysis", technical)
    monkeypatch.setattr("intelligence.council_service._news.collect", collect)
    monkeypatch.setattr("intelligence.council_service._news.summarize", lambda symbol, items: asyncio.sleep(0, result={"sentiment_score": 0, "market_impact": {"severity":"LOW","direction":"MIXED","confidence":50,"score":0}, "items":[]}))
    monkeypatch.setattr("intelligence.council_service._predictor.predict", predict)
    monkeypatch.setattr("intelligence.council_service.depth", depth)
    out = asyncio.run(build_council("BTCUSDT"))
    assert out["symbol"] == "BTCUSDT"
    assert "council" in out and out["council"]["votes"]
    assert out["orderflow"]["imbalance"] > 0
