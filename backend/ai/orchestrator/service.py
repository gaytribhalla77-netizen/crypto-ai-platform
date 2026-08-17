import asyncio
from ai.technical.service import technical_analysis
from ai.news.service import news_analysis
from ai.risk.service import risk_analysis
from ai.regime import detect_regime
from ai.adversarial import challenge_trade
from ai.counterfactual import evaluate_actions
from ai.data_quality import assess_market_data
from ai.validation import model_drift
from ai.consensus import consensus

async def analyze(symbol: str):
    technical, news, risk = await asyncio.gather(
        technical_analysis(symbol), news_analysis(symbol), risk_analysis(symbol)
    )
    closes = technical.get("closes", []) if isinstance(technical, dict) else []
    regime = detect_regime(closes)
    quality = assess_market_data(technical.get("price") if isinstance(technical,dict) else None, len(closes))
    ml = None
    try:
        from ai.ml.predictor import MLPredictor
        ml = await MLPredictor().predict(symbol)
    except Exception:
        ml = {"status":"UNAVAILABLE"}
    cons = consensus(technical, news, risk, ml)
    raw = "BUY" if cons["decision"] == "BUY_BIAS" else "SELL" if cons["decision"] == "SELL_BIAS" else "NO_TRADE"
    confidence = min(100.0, 50.0 + abs(cons["score"])*12.5)
    challenge = challenge_trade(raw, confidence, risk, regime.__dict__, quality)
    entry = float(technical.get("price",0) or 0)
    expected = ((float(ml.get("probability_up",.5))-.5)*2) if ml and ml.get("status")=="OK" else 0.0
    counterfactuals = evaluate_actions(entry, expected, float(risk.get("risk_pct",0) or 0)/100, regime.volatility)
    drift = model_drift([0.0], [0.0])
    if not quality["safe"] or not challenge.approved:
        final="NO_TRADE"
    else:
        final=raw
    return {"symbol":symbol.upper(),"technical":technical,"news":news,"risk":risk,"ml":ml,
            "regime":regime.__dict__,"data_quality":quality,"consensus":cons,
            "adversarial_challenge":challenge.__dict__,"counterfactuals":counterfactuals,"model_drift":drift,
            "decision":final,"confidence":round(confidence,2),
            "safety":"ADVISORY_ONLY_TESTNET"}
