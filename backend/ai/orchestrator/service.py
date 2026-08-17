import asyncio

from ai.adversarial import challenge_trade
from ai.counterfactual import evaluate_actions
from ai.council import IQ200Council
from ai.data_quality import assess_market_data
from ai.news.service import news_analysis
from ai.risk.service import risk_analysis
from ai.regime import detect_regime
from ai.technical.service import technical_analysis
from ai.validation import model_drift


async def analyze(symbol: str):
    """Run the intelligence stack while keeping execution/risk deterministic.

    Gemini-backed research is evidence only. IQ200Council may recommend WAIT,
    but it cannot bypass the canonical risk challenge/firewall.
    """
    technical, news, risk = await asyncio.gather(
        technical_analysis(symbol), news_analysis(symbol), risk_analysis(symbol)
    )

    closes = technical.get("closes", []) if isinstance(technical, dict) else []
    regime = detect_regime(closes)
    quality = assess_market_data(
        technical.get("price") if isinstance(technical, dict) else None,
        len(closes),
    )

    ml = None
    try:
        from ai.ml.predictor import MLPredictor
        ml = await MLPredictor().predict(symbol)
    except Exception:
        ml = {"status": "UNAVAILABLE"}

    council = IQ200Council()
    council_result = council.deliberate_full({
        "technical": technical,
        "news": news,
        "risk": risk,
        "regime": regime.__dict__,
        "ml": ml,
    })

    raw = council_result["chief_judge"]["action"]
    if raw not in {"BUY", "SELL", "WAIT"}:
        raw = "WAIT"
    confidence = float(council_result.get("confidence", 0) or 0)

    challenge = challenge_trade(raw, confidence, risk, regime.__dict__, quality)
    entry = float(technical.get("price", 0) or 0)
    expected = ((float(ml.get("probability_up", 0.5)) - 0.5) * 2) if ml and ml.get("status") == "OK" else 0.0
    counterfactuals = evaluate_actions(
        entry,
        expected,
        float(risk.get("risk_pct", 0) or 0) / 100,
        regime.volatility,
    )
    drift = model_drift([0.0], [0.0])

    if (
        not quality["safe"]
        or council_result.get("veto")
        or council_result.get("contradiction_score", 0)
        or not challenge.approved
        or raw == "WAIT"
    ):
        final = "NO_TRADE"
    else:
        final = raw

    return {
        "symbol": symbol.upper(),
        "technical": technical,
        "news": news,
        "risk": risk,
        "ml": ml,
        "regime": regime.__dict__,
        "data_quality": quality,
        "council": council_result,
        "adversarial_challenge": challenge.__dict__,
        "counterfactuals": counterfactuals,
        "model_drift": drift,
        "decision": final,
        "confidence": round(confidence, 2),
        "safety": "ADVISORY_ONLY_TESTNET",
    }
