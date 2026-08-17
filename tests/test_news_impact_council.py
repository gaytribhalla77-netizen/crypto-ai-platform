from news.impact import NewsImpactAnalyzer
from ai.council import IQ200Council
from ai.historical import analyze_historical_context


def test_market_moving_news_is_detected_and_severity_is_not_just_sentiment():
    out = NewsImpactAnalyzer().analyze([
        {"title": "Major Bitcoin ETF approval announced", "published_at": "2026-08-17T10:00:00+00:00"},
        {"title": "Exchange hack triggers withdrawals", "published_at": "2026-08-17T11:00:00+00:00"},
    ])
    assert out["severity"] in {"CRITICAL", "HIGH"}
    assert out["direction"] in {"MIXED", "BULLISH", "BEARISH"}
    assert out["affected"] is True


def test_historical_context_requires_enough_data():
    assert analyze_historical_context([.01, -.01])['status'] == 'INSUFFICIENT_DATA'
    out = analyze_historical_context([.01] * 30)
    assert out['status'] == 'OK'
    assert out['direction'] == 'BULLISH'


def test_council_includes_historical_and_sentiment_agents():
    out = IQ200Council().deliberate_full({
        "technical": {"score": 1, "trend": "BULLISH"},
        "news": {"sentiment_score": 0.1, "market_impact": {"severity": "HIGH"}},
        "risk": {}, "regime": {"regime": "TREND_UP", "volatility": 0.02},
        "ml": {"status": "NOT_TRAINED"},
        "historical": {"direction": "BULLISH", "confidence": 70},
        "sentiment": {"direction": "BEARISH", "confidence": 70},
    })
    names = {v['name'] for v in out['votes']}
    assert {'historical', 'sentiment'} <= names
    assert out['contradiction_score'] == 1
    assert out['chief_judge']['action'] == 'WAIT'
