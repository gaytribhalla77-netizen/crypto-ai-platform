from ai.council import IQ200Council


def test_step4_research_requires_grounded_evidence_and_keeps_execution_advisory():
    out = IQ200Council().deliberate_full({
        "technical": {"score": 0, "trend": "BULLISH"},
        "news": {
            "impact": "POSITIVE",
            "ai_research": {
                "status": "ok",
                "grounded_sources": [{"url": "https://example.com/news", "title": "Source"}],
                "summary": "Confirmed positive catalyst",
                "impact": "POSITIVE",
                "confidence": 80,
            },
        },
        "risk": {},
        "regime": {"regime": "TREND_UP", "volatility": 0.02},
        "ml": {"status": "NOT_TRAINED"},
    })
    news = next(v for v in out["votes"] if v["name"] == "news")
    assert news["action"] == "BUY"
    assert out["research_policy"]["grounded"] is True
    assert out["execution_authority"] == "DETERMINISTIC_RISK_ENGINE"


def test_step4_unverified_research_cannot_influence_news_vote():
    out = IQ200Council().deliberate_full({
        "technical": {"score": 0, "trend": "WAIT"},
        "news": {
            "impact": "UNKNOWN",
            "ai_research": {
                "status": "ok",
                "grounded_sources": [],
                "summary": "Unverified claim",
                "impact": "POSITIVE",
                "confidence": 100,
            },
        },
        "risk": {},
        "regime": {"regime": "UNKNOWN", "volatility": 0.02},
        "ml": {"status": "NOT_TRAINED"},
    })
    news = next(v for v in out["votes"] if v["name"] == "news")
    assert news["action"] == "WAIT"
    assert out["research_policy"]["grounded"] is False


def test_step4_conflicting_research_and_rss_are_flagged():
    out = IQ200Council().deliberate_full({
        "technical": {"score": 0, "trend": "WAIT"},
        "news": {
            "impact": "NEGATIVE",
            "ai_research": {
                "status": "ok",
                "grounded_sources": [{"url": "https://example.com/news", "title": "Source"}],
                "summary": "Sources indicate a positive catalyst",
                "impact": "POSITIVE",
                "confidence": 85,
            },
        },
        "risk": {},
        "regime": {"regime": "UNKNOWN", "volatility": 0.02},
        "ml": {"status": "NOT_TRAINED"},
    })
    assert out["research_policy"]["conflict"] is True
    assert "research/RSS impact conflict" in out["adversarial_challenge"]["objections"]
    assert out["chief_judge"]["action"] == "WAIT"
