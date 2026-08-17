from fastapi import APIRouter, HTTPException

from news.engine import NewsEngine

router = APIRouter(prefix="/api/news", tags=["news"])
_engine = NewsEngine()


@router.get("/{symbol}")
async def news_for_symbol(symbol: str):
    # Public, read-only — same trust level as GET /api/market/{symbol}.
    try:
        items = await _engine.collect(symbol)
        return await _engine.summarize(symbol, items)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"News unavailable: {e}")
