from market.binance_public import ticker, klines
from ai.technical.indicators import sma, pct_change

async def technical_analysis(symbol: str):
    data = await ticker(symbol)
    candles = await klines(symbol, "1m", 100)
    closes = [float(x[4]) for x in candles]
    price = closes[-1]
    ma20 = sma(closes, 20)
    change_20 = pct_change(closes[-20], price)
    trend = "Bullish" if ma20 and price > ma20 else "Bearish"
    return {
        "symbol": symbol.upper(),
        "price": price,
        "trend": trend,
        "change_20_candles_pct": round(change_20, 3),
        "volume_24h": float(data["volume"]),
        "status": "live_public_market_data",
        "closes": closes,
        "candle_count": len(closes)
    }
