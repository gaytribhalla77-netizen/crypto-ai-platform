import json
import os

import httpx

from news.engine import NewsEngine


_ALLOWED_IMPACTS = {"POSITIVE", "NEGATIVE", "NEUTRAL", "UNKNOWN"}


def _grounded_sources(candidate: dict) -> list[dict]:
    """Return only URLs actually supplied by Gemini grounding metadata."""
    sources: list[dict] = []
    seen: set[str] = set()
    grounding = candidate.get("groundingMetadata", {}) or {}
    for chunk in grounding.get("groundingChunks", []) or []:
        web = chunk.get("web", {}) or {}
        uri = str(web.get("uri", "")).strip()
        if not uri or uri in seen:
            continue
        seen.add(uri)
        sources.append({"url": uri, "title": str(web.get("title", "")).strip()})
    return sources


async def _gemini_web_research(symbol: str, headlines: list[dict]) -> dict:
    """Use Gemini Google Search grounding for fresh research only.

    Gemini is deliberately isolated from trading execution.  The function
    returns evidence and research context; the deterministic risk/execution
    stack remains the only authority for orders.
    """
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        return {"status": "not_configured", "provider": "gemini"}

    model = os.getenv("GEMINI_NEWS_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
    symbol = symbol.upper()
    query = (
        f"Find the latest market-moving news for {symbol}. Focus on the last 24 hours. "
        "Prioritize primary/official sources and reputable financial reporting. Cover "
        "macro, regulation, ETF flows, Fed/RBI, rates, liquidity, geopolitics, hacks "
        "and major company events when relevant. Cross-check important claims. "
        "Do not give a trading order. Return strict JSON with keys: impact, confidence, "
        "summary, catalysts, risks, sources."
    )
    payload = {
        "contents": [{
            "parts": [{"text": json.dumps({"query": query, "rss_headlines": headlines[:12]})}]
        }],
        "systemInstruction": {
            "parts": [{
                "text": (
                    "You are a market research analyst, not a trading executor. "
                    "Use Google Search grounding for current information. Never invent "
                    "a source or claim. If evidence is insufficient or conflicting, "
                    "say so and lower confidence. Return JSON only."
                )
            }]
        },
        "tools": [{"google_search": {}}],
        "generationConfig": {
            "temperature": 0.1,
            "responseMimeType": "application/json",
        },
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params={"key": key}, json=payload)
            response.raise_for_status()
            body = response.json()
    except Exception as exc:
        return {"status": "provider_error", "provider": "gemini", "error": type(exc).__name__}

    candidates = body.get("candidates") or []
    if not candidates:
        return {"status": "empty_model_output", "provider": "gemini", "confidence": 0}

    candidate = candidates[0] or {}
    parts = candidate.get("content", {}).get("parts", []) or []
    text = "".join(str(part.get("text", "")) for part in parts).strip()
    try:
        result = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return {"status": "invalid_model_output", "provider": "gemini", "confidence": 0}
    if not isinstance(result, dict):
        return {"status": "invalid_model_output", "provider": "gemini", "confidence": 0}

    grounded_sources = _grounded_sources(candidate)
    result["sources"] = grounded_sources
    result["grounded_sources"] = grounded_sources
    result["search_queries"] = (candidate.get("groundingMetadata", {}) or {}).get("webSearchQueries", []) or []
    result["provider"] = "gemini"
    result["status"] = "ok"

    impact = str(result.get("impact", "UNKNOWN")).upper()
    result["impact"] = impact if impact in _ALLOWED_IMPACTS else "UNKNOWN"
    try:
        result["confidence"] = max(0.0, min(100.0, float(result.get("confidence", 0))))
    except (TypeError, ValueError):
        result["confidence"] = 0.0

    # Grounding is required for a successful web-research result. The model's
    # free-form `sources` field is intentionally never trusted as evidence.
    if not grounded_sources:
        result["status"] = "no_grounding_evidence"
        result["confidence"] = 0.0
    return result


async def news_analysis(symbol: str):
    """Connect the real RSS news engine to the AI council and Gemini research."""
    engine = NewsEngine()
    items = await engine.collect(symbol)
    rss = await engine.summarize(symbol, items)
    research = await _gemini_web_research(symbol, rss.get("items", []))

    if research.get("status") == "ok":
        return {
            **rss,
            "status": "ok",
            "ai_research": research,
            "impact": research.get("impact", rss.get("impact", "UNKNOWN")),
            "confidence": research.get("confidence", rss.get("confidence", 0)),
            "method": "RSS + Gemini Google Search grounding",
        }

    return {
        **rss,
        "status": "rss_only" if rss.get("count", 0) else research.get("status", "no_data"),
        "ai_research": research,
        "method": "RSS deterministic analysis; Gemini research unavailable",
    }
