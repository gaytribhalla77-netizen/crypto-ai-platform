async def risk_analysis(symbol: str):
    return {
        "symbol": symbol.upper(),
        "risk": "UNKNOWN",
        "status": "risk_engine_baseline_only"
    }
