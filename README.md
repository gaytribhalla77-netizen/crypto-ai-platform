# AI Crypto Trading Platform — V1.6

A web-first development build for an AI crypto market-intelligence/trading platform.

## Included
- Next.js dashboard
- FastAPI backend
- Binance public market-data integration
- Basic technical analysis
- Risk gate
- Paper-trading engine
- Binance adapter boundary for authenticated operations
- Docker/PostgreSQL scaffold
- Telegram + generic webhook notification adapters (optional, fail-safe)
- Request IDs, latency telemetry, shared health registry, and environment validation
- E2E, PostgreSQL, load-smoke, resilience, dependency, and CodeQL validation workflows
- Security and deployment documentation

## Safety
Live trading is OFF by default. Never place broker secrets in frontend code. Use paper trading and testnet development first. Real credentials are supplied only by the operator and the application fails closed when required providers or safety gates are unavailable.

## Run
See `docs/deployment/LOCAL_SETUP.md`.

## Environment validation
Run `python scripts/validate_env.py` before deployment. Production requires a strong JWT secret; live execution has additional explicit gates in `backend/core/config.py` and the real-trading routes.

## Notifications
Set `TELEGRAM_BOT_TOKEN` plus an allowlisted `TELEGRAM_ALLOWED_USER_IDS`, or `NOTIFICATION_WEBHOOK_URL`, to enable optional notifications. Leaving them unset is safe and does not fabricate delivery.

## IQ200 real-provider hardening
Production no longer falls back to mock AI or synthetic FX execution. Real Binance Spot and OANDA v20 adapters are available behind explicit live-trading gates. Missing provider credentials result in fail-closed/no-trade behavior. See `docs/REAL_SYSTEM_STATUS.md`.

## Reliability and Autopsy hardening
See `docs/PRODUCTION_READINESS.md` for the completed hardening items, including observability, environment checks, dependency reproducibility, documentation synchronization, and resilience/load smoke coverage.
