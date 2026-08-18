from ai.council import IQ200Council


def _payload(news):
    return {
        "technical": {"score": 0, "trend": "BULLISH"},
        "news": news,
        "risk": {},
        "regime": {"regime": "TREND_UP", "volatility": 0.02},
        "ml": {"status": "NOT_TRAINED"},
    }


def test_verified_gemini_research_is_bounded_input():
    out = IQ200Council().deliberate_full(_payload({
        "sentiment_score": 0,
        "impact": "POSITIVE",
        "ai_research": {
            "status": "ok",
            "impact": "BULLISH",
            "confidence": 90,
            "summary": "Verified event with grounded evidence.",
            "grounded_sources": [{"url": "https://example.com/a", "title": "A"}],
        },
    }))
    news = next(v for v in out["votes"] if v["name"] == "news")
    assert news["action"] == "BUY"
    assert "Gemini grounded research" in " ".join(news["reasons"])


def test_unverified_gemini_research_cannot_influence_council():
    out = IQ200Council().deliberate_full(_payload({
        "sentiment_score": 0,
        "impact": "POSITIVE",
        "ai_research": {
            "status": "ok",
            "impact": "BEARISH",
            "confidence": 99,
            "summary": "Unverified claim.",
            "grounded_sources": [],
        },
    }))
    news = next(v for v in out["votes"] if v["name"] == "news")
    assert "RSS only" in " ".join(news["reasons"])
    assert "Gemini grounded research" not in " ".join(news["reasons"])


def test_rss_and_grounded_research_conflict_surfaces_as_wait():
    out = IQ200Council().deliberate_full(_payload({
        "sentiment_score": 0,
        "impact": "POSITIVE",
        "ai_research": {
            "status": "ok",
            "impact": "BEARISH",
            "confidence": 100,
            "summary": "Grounded bearish evidence.",
            "grounded_sources": [{"url": "https://example.com/a", "title": "A"}],
        },
    }))
    assert out["contradiction_score"] == 1
    assert out["chief_judge"]["action"] == "WAIT"
    assert out["execution_authority"] == "DETERMINISTIC_RISK_ENGINE"
