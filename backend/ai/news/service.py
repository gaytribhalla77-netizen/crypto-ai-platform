async def news_analysis(symbol: str):
    return {
        "symbol": symbol.upper(),
        "impact": "UNKNOWN",
        "confidence": 0,
        "status": "news_provider_not_configured"
    }
