import json
import os
from typing import Any

import httpx


class FallbackProviderChain:
    """Try configured AI providers in order without changing the caller contract.

    Providers are optional. Missing credentials and provider failures are skipped;
    if none are available the caller receives a fail-closed NO_TRADE result.
    """

    def __init__(self) -> None:
        self.order = [
            p.strip().lower()
            for p in os.getenv("AI_PROVIDER_FALLBACKS", "groq,gemini,openrouter,openai").split(",")
            if p.strip()
        ]

    async def analyze(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        for provider in self.order:
            try:
                result = await self._call(provider, task, context)
                if result and result.get("status") not in {"not_configured", "provider_error"}:
                    result["provider_chain"] = self.order
                    return result
                if result and result.get("status") == "provider_error":
                    errors.append(provider)
            except Exception:
                errors.append(provider)

        return {
            "provider": "fallback_chain",
            "status": "not_configured" if not errors else "all_providers_failed",
            "decision": "NO_TRADE",
            "confidence": 0,
            "risk": 100,
            "reasons": ["No configured AI provider returned a valid analysis."],
            "no_trade_reasons": ["AI provider unavailable; fail-closed."],
            "providers_failed": errors,
        }

    async def _call(self, provider: str, task: str, context: dict[str, Any]) -> dict[str, Any]:
        if provider == "openai":
            return await self._compatible_chat(
                "openai", os.getenv("AI_API_KEY", ""), os.getenv("AI_MODEL", "gpt-4o-mini"),
                "https://api.openai.com/v1/chat/completions"
            , task, context)
        if provider == "groq":
            return await self._compatible_chat(
                "groq", os.getenv("GROQ_API_KEY", ""), os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                "https://api.groq.com/openai/v1/chat/completions", task, context)
        if provider == "openrouter":
            return await self._compatible_chat(
                "openrouter", os.getenv("OPENROUTER_API_KEY", ""),
                os.getenv("OPENROUTER_MODEL", "openrouter/free"),
                "https://openrouter.ai/api/v1/chat/completions", task, context)
        if provider == "gemini":
            return await self._gemini(task, context)
        return {"provider": provider, "status": "not_configured"}

    async def _compatible_chat(self, provider: str, key: str, model: str, url: str,
                               task: str, context: dict[str, Any]) -> dict[str, Any]:
        if not key:
            return {"provider": provider, "status": "not_configured"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Return strict JSON only. Never guarantee profit. If data is insufficient, return NO_TRADE."},
                {"role": "user", "content": json.dumps({"task": task, "context": context})},
            ],
            "temperature": 0.1,
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers={"Authorization": f"Bearer {key}"}, json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"provider": provider, "status": "invalid_model_output", "confidence": 0}

    async def _gemini(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            return {"provider": "gemini", "status": "not_configured"}
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": json.dumps({"task": task, "context": context})}]}],
            "systemInstruction": {"parts": [{"text": "Return strict JSON only. Never guarantee profit. If data is insufficient, return NO_TRADE."}]},
            "generationConfig": {"temperature": 0.1},
        }
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, params={"key": key}, json=payload)
            response.raise_for_status()
            parts = response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [])
            content = "".join(str(p.get("text", "")) for p in parts)
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return {"provider": "gemini", "status": "invalid_model_output", "confidence": 0}
