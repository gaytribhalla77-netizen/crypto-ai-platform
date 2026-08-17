from __future__ import annotations

from ai.council import IQ200Council
from ai.historical import analyze_historical_context
from ai.ml.predictor import MLPredictor
from ai.regime import detect_regime
from ai.technical.service import technical_analysis
from market.binance_public import depth
from news.engine import NewsEngine
from knowledge.engine import TradingKnowledgeEngine

_council = IQ200Council()
_news = NewsEngine()
_predictor = MLPredictor()
_knowledge = TradingKnowledgeEngine()


async def build_council(symbol: str) -> dict:
    symbol = symbol.upper()
    technical = await technical_analysis(symbol)
    news_items = await _news.collect(symbol)
    news = await _news.summarize(symbol, news_items)
    ml = await _predictor.predict(symbol)
    closes = [float(x) for x in technical.get("closes", []) if float(x) > 0]
    returns = [(b - a) / a for a, b in zip(closes, closes[1:]) if a]
    historical = analyze_historical_context(returns, horizon=min(20, len(returns)))
    regime_obj = detect_regime(closes)
    regime = {
        "regime": regime_obj.name,
        "confidence": regime_obj.confidence,
        "volatility": regime_obj.volatility,
        "trend_strength": regime_obj.trend_strength,
        "reason": regime_obj.reason,
    }
    try:
        raw = await depth(symbol, 100)
        total = float(raw.get("bid_notional", 0)) + float(raw.get("ask_notional", 0))
        imbalance = (float(raw.get("bid_notional", 0)) - float(raw.get("ask_notional", 0))) / total if total else 0.0
        orderflow = {"imbalance": imbalance, **raw}
    except Exception:
        orderflow = {"status": "UNAVAILABLE"}
    macro = {
        "risk_score": 1.0 if news.get("market_impact", {}).get("severity") == "CRITICAL" else .8 if news.get("market_impact", {}).get("severity") == "HIGH" else 0.0,
        "surprise_score": news.get("market_impact", {}).get("score", 0),
        "source": "news market-impact layer",
    }
    sentiment = {
        "direction": news.get("market_impact", {}).get("direction", "NEUTRAL"),
        "confidence": news.get("market_impact", {}).get("confidence", 0),
    }
    risk = {"status": "DEFER_TO_EXECUTION_RISK_ENGINE"}
    knowledge_gate = _knowledge.evaluate_setup(market={"symbol": symbol, "regime": regime}, news=news, risk=risk)
    council = _council.deliberate_full({
        "technical": technical, "news": news, "risk": risk, "regime": regime,
        "ml": ml, "orderflow": orderflow, "macro": macro,
        "historical": historical, "sentiment": sentiment,
    })
    # Hard market-moving news veto: the council must wait rather than infer
    # a directional trade from a critical event.
    if news.get("market_impact", {}).get("severity") == "CRITICAL":
        council["chief_judge"]["action"] = "WAIT"
        council["veto"] = True
        council["adversarial_challenge"]["objections"].append("critical market-moving news requires confirmation")
    return {
        "symbol": symbol,
        "technical": technical,
        "news": news,
        "ml": ml,
        "historical": historical,
        "regime": regime,
        "orderflow": orderflow,
        "macro": macro,
        "sentiment": sentiment,
        "council": council,
        "knowledge_gate": knowledge_gate,
        "trade_ready": council.get("chief_judge", {}).get("action") in {"BUY", "SELL"} and not council.get("veto") and knowledge_gate["status"] == "ELIGIBLE_FOR_RISK_REVIEW",
        "disclaimer": "Council output is probabilistic evidence, not a profit guarantee. Execution must still pass risk, protection, idempotency and live confirmation gates.",
    }
