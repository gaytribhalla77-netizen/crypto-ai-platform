import pytest

from backend.ai.providers.fallback_provider import FallbackProviderChain


@pytest.mark.asyncio
async def test_gateway_fails_closed_without_credentials(monkeypatch):
    for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY", "AI_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("AI_PROVIDER_FALLBACKS", "groq,gemini,openrouter,openai")
    monkeypatch.setenv("AI_PROVIDER_MODE", "fallback")
    result = await FallbackProviderChain().analyze("analyze", {"symbol": "BTCUSDT"})
    assert result["decision"] == "NO_TRADE"
    assert result["risk"] == 100
    assert result["providers_attempted"] == ["groq", "gemini", "openrouter", "openai"]


@pytest.mark.asyncio
async def test_ensemble_disagreement_fails_closed(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER_FALLBACKS", "groq,gemini")
    monkeypatch.setenv("AI_PROVIDER_MODE", "ensemble")
    gateway = FallbackProviderChain()

    async def fake_call(provider, task, context):
        return {
            "provider": provider,
            "status": "ok",
            "decision": "BUY" if provider == "groq" else "SELL",
            "confidence": 90,
            "risk": 20,
            "reasons": [provider],
        }

    monkeypatch.setattr(gateway, "_call", fake_call)
    result = await gateway.analyze("analyze", {"symbol": "BTCUSDT"})
    assert result["decision"] == "NO_TRADE"
    assert "Provider disagreement" in result["no_trade_reasons"][0]


def test_normalization_rejects_invalid_decision_and_bounds_numbers():
    result = FallbackProviderChain._normalize(
        {"decision": "YOLO", "confidence": 900, "risk": -5}, "test"
    )
    assert result["decision"] == "NO_TRADE"
    assert result["confidence"] == 100
    assert result["risk"] == 0
