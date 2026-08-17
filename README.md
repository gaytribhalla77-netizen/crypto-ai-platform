# AI Crypto Trading Platform — V1.6

A web-first development build for an AI crypto market-intelligence/trading platform.

See `docs/trading/V1_6_FIXES.md` for exactly what changed since the v1.5
audit, including a section on what is still not production-ready.


## Included
- Next.js dashboard
- FastAPI backend
- Binance public market-data integration
- Basic technical analysis
- Risk gate
- Paper-trading engine
- Binance adapter boundary for authenticated operations
- Docker/PostgreSQL scaffold
- Telegram/voice architecture placeholders
- Security and deployment documentation

## Safety
Live trading is OFF. This build does not contain working live-order execution.
Use paper trading and testnet development first.

## Run
See `docs/deployment/LOCAL_SETUP.md`.


## IQ200 real-provider hardening

Production no longer falls back to mock AI or synthetic FX execution. Real Binance Spot and OANDA v20 adapters are available behind explicit live-trading gates. Missing provider credentials result in fail-closed/no-trade behavior. See `docs/REAL_SYSTEM_STATUS.md`.

## IQ200+ Research and Reliability Layer
Added after external architecture survey: purged/embargoed validation, uncertainty intervals, evidence-based pattern discovery, dataset lineage/fingerprints, real execution-quality metrics, fail-closed trading circuit breakers, macro-event impact measurement, and deterministic event replay fingerprints.
