import os
from core.config import settings


class TelegramCommandCenter:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        # Empty allowlist = deny everyone by default (fail closed), not
        # "allow everyone" — an operator must explicitly configure
        # TELEGRAM_ALLOWED_USER_IDS before this bot will respond to anyone.
        self.allowed_user_ids = set(settings.telegram_allowed_user_ids)

    def _is_authorized(self, user_id) -> bool:
        return str(user_id) in self.allowed_user_ids

    async def handle(self, text, user_id):
        if not self._is_authorized(user_id):
            # Spec requirement: unknown Telegram user -> DENY. Previously
            # this method accepted any user_id and replied normally.
            return "Unauthorized. This bot is restricted to allow-listed users."

        t = text.strip()
        if not t:
            return "Command खाली है."
        if t.lower() in {"help", "/help"}:
            return "Commands: /market BTCUSDT, /analyze BTCUSDT, /paper BUY BTCUSDT 5"
        return "Command received. Production Telegram webhook/adapter should route this to the same CO API."
