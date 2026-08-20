import pytest

from backend.notifications import NotificationService


@pytest.mark.asyncio
async def test_notification_service_fails_closed_without_configuration(monkeypatch):
    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_ALLOWED_USER_IDS", "NOTIFICATION_WEBHOOK_URL"):
        monkeypatch.delenv(key, raising=False)
    result = await NotificationService().send("test")
    assert result[0].sent is False
    assert result[0].channel == "none"
