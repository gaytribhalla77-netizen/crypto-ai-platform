from ai.providers.fallback_provider import FallbackProviderChain


class ChiefOperator:
    """Provider-independent AI boundary with fail-closed trading decisions."""

    def __init__(self):
        self.provider = FallbackProviderChain()

    @property
    def configured(self):
        return bool(self.provider.order)

    async def analyze(self, symbol, market, news, risk):
        result = await self.provider.analyze(
            "Analyze this trading setup. Return strict JSON with decision BUY, SELL or NO_TRADE, confidence 0-100, risk 0-100, reasons, invalidation, and no_trade_reasons. Never invent missing market data and never guarantee profit.",
            {"symbol": symbol, "market": market, "news": news, "risk": risk},
        )
        decision = str(result.get("decision", "NO_TRADE")).upper()
        if decision not in {"BUY", "SELL", "NO_TRADE"}:
            decision = "NO_TRADE"
        result["decision"] = decision
        try:
            result["confidence"] = max(0, min(100, float(result.get("confidence", 0))))
        except (TypeError, ValueError):
            result["confidence"] = 0
        return result
