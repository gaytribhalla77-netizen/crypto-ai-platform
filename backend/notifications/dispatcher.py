from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class DeliveryResult:
    channel: str
    ok: bool
    detail: str


class NotificationDispatcher:
    """Fail-closed notification delivery with bounded network timeouts."""

    def __init__(self, timeout_seconds: float = 8.0) -> None:
        self.timeout_seconds = timeout_seconds

    async def send(self, message: str, *, user_id: str | None = None) -> list[DeliveryResult]:
        results: list[DeliveryResult] = []
        webhook = os.getenv("NOTIFICATION_WEBHOOK_URL", "").strip()
        telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

        if webhook:
            results.append(await self._webhook(webhook, message))
        if telegram_token and telegram_chat_id:
            results.append(await self._telegram(telegram_token, telegram_chat_id, message))

        if not results:
            results.append(DeliveryResult("none", False, "No notification provider configured"))
        return results

    async def _webhook(self, url: str, message: str) -> DeliveryResult:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=False) as client:
                response = await client.post(url, json={"message": message})
            if 200 <= response.status_code < 300:
                return DeliveryResult("webhook", True, f"HTTP {response.status_code}")
            return DeliveryResult("webhook", False, f"HTTP {response.status_code}")
        except Exception as exc:
            return DeliveryResult("webhook", False, type(exc).__name__)

    async def _telegram(self, token: str, chat_id: str, message: str) -> DeliveryResult:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds, follow_redirects=False) as client:
                response = await client.post(url, json={"chat_id": chat_id, "text": message})
            if 200 <= response.status_code < 300:
                return DeliveryResult("telegram", True, "delivered")
            return DeliveryResult("telegram", False, f"HTTP {response.status_code}")
        except Exception as exc:
            return DeliveryResult("telegram", False, type(exc).__name__)


notifications = NotificationDispatcher()
