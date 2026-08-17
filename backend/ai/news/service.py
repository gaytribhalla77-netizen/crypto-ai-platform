import json
import os

import httpx

from news.engine import NewsEngine


async def _gemini_web_research(symbol: str, headlines: list[dict]) -> dict:
    """Use Gemini Google Search grounding for fresh news research only."""
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        return {"status": "not_configured", "provider": "gemini"}

    model = os.getenv("GEMINI_NEWS_MODEL", os.getenv("GEMINI_MODEL", "gemini-2.0-flash"))
    symbol = symbol.upper()
    query = (
        f"Find the latest market-moving news for {symbol}. "
        "Focus on the last 24 hours and include macro, regulation, ETF, "
        "Fed/RBI, rates, liquidity, geopolitics, hacks and major company events "
        "when relevant. Cross-check important claims and cite sources. "
        "Do not give a trading order. Return strict JSON with keys: "
        "impact, confidence, summary, catalysts, risks, sources."
    )
    payload = {
        "contents": [{
            "parts": [{"text": json.dumps({"query": query, "rss_headlines": headlines[:12]})}]
        }],
        "systemInstruction": {
            "parts": [{
                "text": (
                    "You are a market research analyst, not a trading executor. "
                    "Use Google Search grounding for current information. "
                    "Never invent a source. If evidence is insufficient, say so. "
                    "Return JSON only."
                )
            }]
        },
        "tools": [{"google_search": {}}],
        "generationConfig": {"temperature": 0.1},
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params={"key": key}, json=payload)
            response.raise_for_status()
            body = response.json()
    except Exception as exc:
        return {"status": "provider_error", "provider": "gemini", "error": type(exc).__name__}

    candidate = body.get("candidates", [{}])[0]
    parts = candidate.get("content", {}).get("parts", [])
    text = "".join(str(part.get("text", "")) for part in parts).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        return {"status": "invalid_model_output", "provider": "gemini", "confidence": 0}
    if not isinstance(result, dict):
        return {"status": "invalid_model_output", "provider": "gemini", "confidence": 0}

    grounding = candidate.get("groundingMetadata", {}) or {}
    grounded_sources = []
    for chunk in grounding.get("groundingChunks", []) or []:
        web = chunk.get("web", {})
        if web.get("uri"):
            grounded_sources.append({"url": web["uri"], "title": web.get("title", "")})
    result["sources"] = result.get("sources") or grounded_sources
    result["grounded_sources"] = grounded_sources
    result["search_queries"] = grounding.get("webSearchQueries", [])
    result["provider"] = "gemini"
    result["status"] = "ok"
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
