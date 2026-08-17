import os
from ai.providers.openai_provider import OpenAIProvider


class ChiefOperator:
    """Real-provider-only AI boundary. Never substitutes a fake model response."""
    def __init__(self):
        self.provider = OpenAIProvider()

    @property
    def configured(self):
        return bool(os.getenv("AI_API_KEY", ""))

    async def analyze(self, symbol, market, news, risk):
        if not self.configured:
            return {"provider": "openai", "status": "not_configured", "decision": "NO_TRADE", "confidence": 0, "reason": "AI provider credentials are not configured."}
        result = await self.provider.analyze(
            "Analyze this trading setup. Return strict JSON with decision BUY, SELL or NO_TRADE, confidence 0-100, risk 0-100, reasons, invalidation, and no_trade_reasons. Never invent missing market data and never guarantee profit.",
            {"symbol": symbol, "market": market, "news": news, "risk": risk}
        )
        decision = str(result.get("decision", "NO_TRADE")).upper()
        if decision not in {"BUY", "SELL", "NO_TRADE"}: decision = "NO_TRADE"
        result["decision"] = decision
        result["confidence"] = max(0, min(100, float(result.get("confidence", 0))))
        return result
