import os
from dataclasses import dataclass

_DEV_DEFAULT_SECRET = "dev-only-insecure-secret-change-me"


@dataclass(frozen=True)
class Settings:
    app_env: str = os.getenv("APP_ENV", "development").lower()
    live_trading: bool = os.getenv("LIVE_TRADING", "false").lower() == "true"
    paper_trading: bool = os.getenv("PAPER_TRADING", "false").lower() == "true"
    auto_opportunity_enabled: bool = os.getenv("AUTO_OPPORTUNITY_ENABLED", "false").lower() == "true"
    auto_opportunity_max_usdt: float = float(os.getenv("AUTO_OPPORTUNITY_MAX_USDT", "10"))
    stop_loss_percent: float = float(os.getenv("DEFAULT_STOP_LOSS_PERCENT", "5"))
    take_profit_percent: float = float(os.getenv("DEFAULT_TAKE_PROFIT_PERCENT", "5"))
    secret_key: str = os.getenv("JWT_SECRET_KEY", _DEV_DEFAULT_SECRET)
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    telegram_allowed_user_ids: tuple = tuple(
        x.strip() for x in os.getenv("TELEGRAM_ALLOWED_USER_IDS", "").split(",") if x.strip()
    )
    enable_workers: bool = os.getenv("ENABLE_WORKERS", "false").lower() == "true"
    single_operator_mode: bool = os.getenv("SINGLE_OPERATOR_MODE", "false").lower() == "true"
    broker: str = os.getenv("BROKER", "binance").lower()
    oanda_practice: bool = os.getenv("OANDA_PRACTICE", "true").lower() == "true"
    live_confirmation: str = os.getenv("LIVE_TRADING_CONFIRM", "")
    watchlist_symbols: tuple = tuple(
        x.strip().upper() for x in os.getenv("WATCHLIST_SYMBOLS", "BTCUSDT,ETHUSDT").split(",") if x.strip()
    )


settings = Settings()

if settings.app_env in {"production", "prod"} and settings.secret_key == _DEV_DEFAULT_SECRET:
    raise RuntimeError("Production requires a strong JWT_SECRET_KEY; refusing the insecure development default.")

if settings.live_trading and settings.secret_key == _DEV_DEFAULT_SECRET:
    raise RuntimeError(
        "LIVE_TRADING is true but JWT_SECRET_KEY was not set. Refusing to start "
        "with the insecure default secret in a live-trading configuration."
    )

if settings.live_trading:
    if settings.broker not in {"binance", "oanda"}:
        raise RuntimeError("LIVE_TRADING requires BROKER=binance or BROKER=oanda.")
    # Multi-user deployments keep broker credentials in the encrypted vault,
    # so global broker keys are not required at startup. Single-operator mode
    # may use environment credentials as a deliberate fallback.
    if settings.single_operator_mode:
        if settings.broker == "binance" and not (os.getenv("BINANCE_API_KEY") and os.getenv("BINANCE_API_SECRET")):
            raise RuntimeError("SINGLE_OPERATOR_MODE + LIVE_TRADING requires Binance environment credentials.")
        if settings.broker == "oanda" and not (os.getenv("OANDA_API_TOKEN") and os.getenv("OANDA_ACCOUNT_ID")):
            raise RuntimeError("SINGLE_OPERATOR_MODE + LIVE_TRADING requires OANDA environment credentials.")
    if not settings.enable_workers:
        raise RuntimeError("LIVE_TRADING=true requires ENABLE_WORKERS=true so reconciliation and protection monitoring are active.")
    if os.getenv("LIVE_TRADING_CONFIRM", "") != "I_UNDERSTAND_LIVE_TRADING":
        raise RuntimeError("LIVE_TRADING=true requires LIVE_TRADING_CONFIRM=I_UNDERSTAND_LIVE_TRADING.")
