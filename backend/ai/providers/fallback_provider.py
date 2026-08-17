import asyncio
import json
import os
import time
from typing import Any

import httpx


class FallbackProviderChain:
    """Provider-independent AI gateway with fallback and optional consensus.

    Missing credentials and provider failures are skipped. If no provider can
    produce a valid decision, the result is always NO_TRADE.
    """

    def __init__(self) -> None:
        self.order = [
            p.strip().lower()
            for p in os.getenv(
                "AI_PROVIDER_FALLBACKS", "groq,gemini,openrouter,openai"
            ).split(",")
            if p.strip()
        ]
        self.mode = os.getenv("AI_PROVIDER_MODE", "fallback").strip().lower()
        try:
            configured_timeout = float(os.getenv("AI_PROVIDER_TIMEOUT_SECONDS", "20"))
        except (TypeError, ValueError):
            configured_timeout = 20.0
        self.timeout = max(5.0, min(60.0, configured_timeout))

    async def analyze(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        if self.mode == "ensemble":
            return await self._ensemble(task, context)
        return await self._fallback(task, context)

    async def _fallback(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        errors: list[str] = []
        attempted: list[str] = []
        started = time.perf_counter()
        for provider in self.order:
            attempted.append(provider)
            try:
                result = self._normalize(
                    await self._call(provider, task, context), provider
                )
                if result.get("status") not in {
                    "not_configured",
                    "provider_error",
                    "invalid_model_output",
                }:
                    result["provider_used"] = provider
                    result["provider_chain"] = self.order
                    result["providers_attempted"] = attempted
                    result["latency_ms"] = round(
                        (time.perf_counter() - started) * 1000, 2
                    )
                    return result
                errors.append(provider)
            except Exception:
                errors.append(provider)

        return self._no_trade(errors, attempted, started)

    async def _ensemble(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        started = time.perf_counter()
        providers = list(self.order)
        results = await asyncio.gather(
            *(self._safe_call(provider, task, context) for provider in providers)
        )
        valid = [
            self._normalize(result, provider)
            for provider, result in zip(providers, results)
            if result
        ]
        valid = [
            result
            for result in valid
            if result.get("status")
            not in {"not_configured", "provider_error", "invalid_model_output"}
        ]
        if not valid:
            return self._no_trade(providers, providers, started)

        votes: dict[str, float] = {"BUY": 0.0, "SELL": 0.0, "NO_TRADE": 0.0}
        for result in valid:
            votes[result["decision"]] += float(result["confidence"])
        decision = max(votes, key=votes.get)
        agreeing = [r for r in valid if r["decision"] == decision]
        confidence = sum(float(r["confidence"]) for r in agreeing) / max(
            1, len(agreeing)
        )
        if len(agreeing) < 2 and len(valid) > 1:
            decision = "NO_TRADE"
            confidence = 0.0
        return {
            "provider": "ensemble",
            "provider_mode": "ensemble",
            "providers_used": [r.get("provider") for r in valid],
            "providers_attempted": providers,
            "decision": decision,
            "confidence": round(max(0.0, min(100.0, confidence)), 2),
            "risk": max(float(r.get("risk", 100)) for r in valid),
            "reasons": sum((r.get("reasons", []) for r in agreeing), [])[:12],
            "no_trade_reasons": (
                ["Provider disagreement; ensemble fail-closed."]
                if decision == "NO_TRADE"
                else []
            ),
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    async def _safe_call(
        self, provider: str, task: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            return await self._call(provider, task, context)
        except Exception:
            return {"provider": provider, "status": "provider_error"}

    def _no_trade(
        self, errors: list[str], attempted: list[str], started: float
    ) -> dict[str, Any]:
        return {
            "provider": "fallback_chain",
            "status": "not_configured" if not errors else "all_providers_failed",
            "decision": "NO_TRADE",
            "confidence": 0,
            "risk": 100,
            "reasons": ["No configured AI provider returned a valid analysis."],
            "no_trade_reasons": ["AI provider unavailable; fail-closed."],
            "providers_failed": errors,
            "providers_attempted": attempted,
            "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }

    @staticmethod
    def _normalize(result: dict[str, Any], provider: str) -> dict[str, Any]:
        result = dict(result or {})
        result["provider"] = provider
        decision = str(result.get("decision", "NO_TRADE")).upper()
        result["decision"] = (
            decision if decision in {"BUY", "SELL", "NO_TRADE"} else "NO_TRADE"
        )
        try:
            result["confidence"] = max(
                0.0, min(100.0, float(result.get("confidence", 0)))
            )
        except (TypeError, ValueError):
            result["confidence"] = 0.0
        try:
            result["risk"] = max(0.0, min(100.0, float(result.get("risk", 100))))
        except (TypeError, ValueError):
            result["risk"] = 100.0
        result.setdefault("reasons", [])
        result.setdefault("no_trade_reasons", [])
        return result

    async def _call(
        self, provider: str, task: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        if provider == "openai":
            return await self._compatible_chat(
                "openai",
                os.getenv("AI_API_KEY", ""),
                os.getenv("AI_MODEL", "gpt-4o-mini"),
                "https://api.openai.com/v1/chat/completions",
                task,
                context,
            )
        if provider == "groq":
            return await self._compatible_chat(
                "groq",
                os.getenv("GROQ_API_KEY", ""),
                os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
                "https://api.groq.com/openai/v1/chat/completions",
                task,
                context,
            )
        if provider == "openrouter":
            return await self._compatible_chat(
                "openrouter",
                os.getenv("OPENROUTER_API_KEY", ""),
                os.getenv("OPENROUTER_MODEL", "openrouter/free"),
                "https://openrouter.ai/api/v1/chat/completions",
                task,
                context,
            )
        if provider == "gemini":
            return await self._gemini(task, context)
        return {"provider": provider, "status": "not_configured"}

    async def _compatible_chat(
        self,
        provider: str,
        key: str,
        model: str,
        url: str,
        task: str,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        if not key:
            return {"provider": provider, "status": "not_configured"}
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Return strict JSON only. Never guarantee profit. If data is insufficient, return NO_TRADE.",
                },
                {
                    "role": "user",
                    "content": json.dumps({"task": task, "context": context}),
                },
            ],
            "temperature": 0.1,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url, headers={"Authorization": f"Bearer {key}"}, json=payload
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        return self._parse_json(content, provider)

    async def _gemini(self, task: str, context: dict[str, Any]) -> dict[str, Any]:
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            return {"provider": "gemini", "status": "not_configured"}
        model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent"
        )
        payload = {
            "contents": [
                {"parts": [{"text": json.dumps({"task": task, "context": context})}]}
            ],
            "systemInstruction": {
                "parts": [
                    {
                        "text": "Return strict JSON only. Never guarantee profit. If data is insufficient, return NO_TRADE."
                    }
                ]
            },
            "generationConfig": {"temperature": 0.1},
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, params={"key": key}, json=payload)
            response.raise_for_status()
            parts = (
                response.json()
                .get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [])
            )
            content = "".join(str(p.get("text", "")) for p in parts)
        return self._parse_json(content, "gemini")

    @staticmethod
    def _parse_json(content: str, provider: str) -> dict[str, Any]:
        text = str(content or "").strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            parsed = json.loads(text)
            return (
                parsed
                if isinstance(parsed, dict)
                else {"provider": provider, "status": "invalid_model_output"}
            )
        except json.JSONDecodeError:
            return {
                "provider": provider,
                "status": "invalid_model_output",
                "confidence": 0,
            }
