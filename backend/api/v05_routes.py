from fastapi import APIRouter
from ai.brain import ChiefOperator
from news.engine import NewsEngine
from trading.position_monitor import PositionMonitor

router = APIRouter(prefix="/api/v05", tags=["v0.5"])
brain = ChiefOperator()
news = NewsEngine()

@router.get("/intelligence/{symbol}")
async def intelligence(symbol: str):
    # The route is wired for orchestration; live news/AI providers remain fail-closed.
    from ai.technical.service import technical_analysis
    market = await technical_analysis(symbol)
    items = await news.collect(symbol)
    news_summary = await news.summarize(symbol, items)
    risk = {"risk": "UNKNOWN", "status": "baseline"}
    return await brain.analyze(symbol, market, news_summary, risk)
