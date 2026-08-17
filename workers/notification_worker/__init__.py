"""Notification-dispatch worker.

Previously an empty file. Provides a queue other workers can push events
onto, applies NotificationService's priority-escalation filter, and logs
the result. IMPORTANT: this does not implement an actual delivery channel
(Telegram/email/SMS/push) — that adapter doesn't exist yet in this build.
Treat this as the dispatch pipeline's plumbing, not a working alert system.
"""
import asyncio
import logging

from notifications.service import NotificationService

logger = logging.getLogger("workers.notification_worker")


class NotificationWorker:
    def __init__(self):
        self.service = NotificationService()
        self.queue: asyncio.Queue = asyncio.Queue()
        self._last_priority_by_type: dict[str, str] = {}

    async def enqueue(self, event_type: str, priority: str, payload: dict):
        await self.queue.put((event_type, priority, payload))

    async def run_once(self, timeout: float = 1.0):
        try:
            event_type, priority, payload = await asyncio.wait_for(self.queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None
        last = self._last_priority_by_type.get(event_type)
        if not self.service.should_send(priority, last):
            return None
        self._last_priority_by_type[event_type] = priority
        result = await self.service.event(event_type, priority, payload)
        # No real delivery channel wired up yet — log only.
        logger.info("NOTIFY (undelivered — no channel configured): %s", result)
        return result

    async def run_forever(self):
        while True:
            await self.run_once()
