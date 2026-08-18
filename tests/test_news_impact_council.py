from ai.council import IQ200Council
from ai.historical import analyze_historical_context
from ai.news.service import _grounded_sources, _research_is_usable
from news.impact import NewsImpactAnalyzer


def test_market_moving_news_is_detected_and_severity_is_not_just_sentiment():
    out = NewsImpactAnalyzer().analyze([
        {"title": "Major Bitcoin ETF approval announced", "published_at": "2026-08-17T10:00:00+00:00"},
        {"title": "Exchange hack triggers withdrawals", "published_at": "2026-08-17T11:00:00+00:00"},
    ])
    assert out["severity"] in {"CRITICAL", "HIGH"}
    assert out["direction"] in {"MIXED", "BULLISH", "BEARISH"}
    assert out["affected"] is True


def test_historical_context_requires_enough_data():
    assert analyze_historical_context([.01, -.01])["status"] == "INSUFFICIENT_DATA"
    out = analyze_historical_context([.01] * 30)
    assert out["status"] == "OK"
    assert out["direction"] == "BULLISH"


def test_council_normalizes_technical_trend_and_uses_news_impact():
    out = IQ200Council().deliberate_full({
        "technical": {"score": 0, "trend": "Bullish"},
        "news": {"sentiment_score": 0, "impact": "POSITIVE"},
        "risk": {},
        "regime": {"regime": "TREND_UP", "volatility": 0.02},
        "ml": {"status": "NOT_TRAINED"},
    })
    technical = next(v for v in out["votes"] if v["name"] == "technical")
    news = next(v for v in out["votes"] if v["name"] == "news")
    assert technical["action"] == "BUY"
    assert news["action"] == "BUY"


def test_council_includes_historical_and_sentiment_agents():
    out = IQ200Council().deliberate_full({
        "technical": {"score": 1, "trend": "BULLISH"},
        "news": {"sentiment_score": 0.1, "market_impact": {"severity": "HIGH"}},
        "risk": {}, "regime": {"regime": "TREND_UP", "volatility": 0.02},
        "ml": {"status": "NOT_TRAINED"},
        "historical": {"direction": "BULLISH", "confidence": 70},
        "sentiment": {"direction": "BEARISH", "confidence": 70},
    })
    names = {v["name"] for v in out["votes"]}
    assert {"historical", "sentiment"} <= names
    assert out["contradiction_score"] == 1
    assert out["chief_judge"]["action"] == "WAIT"


def test_grounded_sources_only_accept_valid_web_urls_and_deduplicate():
    candidate = {
        "groundingMetadata": {
            "groundingChunks": [
                {"web": {"uri": "https://example.com/a", "title": "A"}},
                {"web": {"uri": "https://example.com/a", "title": "A duplicate"}},
                {"web": {"uri": "http://example.com/b", "title": "B"}},
                {"web": {"uri": "javascript:alert(1)", "title": "bad"}},
                {"text": "not a web source"},
            ]
        }
    }
    assert _grounded_sources(candidate) == [
        {"url": "https://example.com/a", "title": "A"},
        {"url": "http://example.com/b", "title": "B"},
    ]


def test_research_is_fail_closed_without_grounded_evidence_or_summary():
    base = {
        "status": "ok", "impact": "POSITIVE", "confidence": 80,
        "grounded_sources": [{"url": "https://example.com", "title": "source"}],
    }
    assert not _research_is_usable(base)
    base["summary"] = "Verified market-moving event."
    assert _research_is_usable(base)
    base["confidence"] = 101
    assert not _research_is_usable(base)
