from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class NotificationResult:
    channel: str
    sent: bool
    detail: str


class NotificationService:
    PRIORITY = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}

    def should_send(self, priority, last_priority=None):
        if priority not in self.PRIORITY:
            return False
        return last_priority is None or self.PRIORITY[priority] >= self.PRIORITY.get(last_priority, 0)

    async def event(self, event_type, priority, payload):
        return {"event": event_type, "priority": priority, "payload": payload}

    async def send(self, message: str, *, user_id: str | None = None):
        """Return a safe delivery result; actual delivery is delegated to configured adapters."""
        if os.getenv("TELEGRAM_BOT_TOKEN", "").strip() and os.getenv("TELEGRAM_CHAT_ID", "").strip():
            return [NotificationResult("telegram", False, "delivery handled by dispatcher")]
        if os.getenv("NOTIFICATION_WEBHOOK_URL", "").strip():
            return [NotificationResult("webhook", False, "delivery handled by dispatcher")]
        return [NotificationResult("none", False, "No notification provider configured")]
