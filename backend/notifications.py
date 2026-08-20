from __future__ import annotations

import os
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class NotificationResult:
    sent: bool
    channel: str
    detail: str


class NotificationService:
    """Fail-safe notification adapters. Missing credentials never raise."""

    def __init__(self) -> None:
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.telegram_users = tuple(
            x.strip() for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",") if x.strip()
        )
        self.webhook_url = os.getenv("NOTIFICATION_WEBHOOK_URL", "").strip()
        self.timeout = float(os.getenv("NOTIFICATION_TIMEOUT_SECONDS", "5"))

    async def send(self, message: str, *, user_id: str | None = None) -> list[NotificationResult]:
        results: list[NotificationResult] = []
        if self.telegram_token and self.telegram_users:
            recipients = (str(user_id),) if user_id and str(user_id) in self.telegram_users else self.telegram_users
            for recipient in recipients:
                url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
                try:
                    async with httpx.AsyncClient(timeout=self.timeout) as client:
                        response = await client.post(url, json={"chat_id": recipient, "text": message[:4096]})
                        response.raise_for_status()
                    results.append(NotificationResult(True, "telegram", f"delivered:{recipient}"))
                except Exception as exc:
                    results.append(NotificationResult(False, "telegram", type(exc).__name__))
        if self.webhook_url:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(self.webhook_url, json={"message": message})
                    response.raise_for_status()
                results.append(NotificationResult(True, "webhook", "delivered"))
            except Exception as exc:
                results.append(NotificationResult(False, "webhook", type(exc).__name__))
        if not results:
            results.append(NotificationResult(False, "none", "no notification provider configured"))
        return results


notifications = NotificationService()
