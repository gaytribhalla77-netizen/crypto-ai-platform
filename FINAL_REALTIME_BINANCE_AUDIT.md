# IQ200 — Real-Time Binance Intelligence & Live Trading Audit

## Scope
This round integrates the video-inspired requirement as a real backend feature: continuous Binance market telemetry, live news/market-impact monitoring, real evidence-based council analysis, and a non-executing alert stream. It is explicitly designed for Binance spot trading; the monitoring layer never places orders.

## Added
- Binance public `bookTicker` WebSocket stream for configured watchlist symbols.
- Authenticated `/api/realtime/status` endpoint.
- Authenticated WebSocket `/api/realtime/stream` using first-message JWT authentication (token is not put in the URL).
- Live technical refresh and news refresh.
- Crypto news plus official Federal Reserve and SEC RSS sources for market-moving macro/regulatory context.
- High/critical market-moving news alerts.
- Live public Binance order-book depth (the previous orderbook helper was Testnet-only and is no longer used for live council evidence).
- Real council evidence package combining technicals, news impact, historical context, regime, order-book imbalance, optional trained ML, macro proxy, and sentiment proxy.
- Critical-news veto forcing `WAIT`.
- Opportunity scanner no longer uses placeholder confidence/risk numbers; it consumes council evidence and remains non-executing.
- Dashboard real-time monitor UI.
- Voice trading path now detects live mode and uses the live Binance endpoint with a fresh TOTP code rather than always calling the Testnet route.

## Safety boundary
Real-time monitoring and council analysis cannot place an order. Actual live execution remains behind authentication, TOTP, kill switch, risk validation, Binance filters, idempotency, exchange-side protection, reconciliation, and explicit live configuration.

## Test results
- Full Python suite: **53 passed, 2 environment-blocked**.
- Blocked tests: both SQLite idempotency tests require `aiosqlite`, which is declared in `backend/requirements.txt` but is not installed in this audit environment.
- New/affected focused suite: **21 passed**.
- Python compileall: **PASS**.
- Backend app import could not complete in this environment for the same missing `aiosqlite` dependency.
- Frontend TypeScript/build could not be certified because `node_modules` is absent. `tsc` additionally reports pre-existing project errors unrelated to the realtime monitor.

## No false certification
This audit certifies the code paths that could be executed in the available environment. It does not claim that a live Binance account, network, exchange-side OCO behavior, or production browser build was exercised here.

## Source coverage limitation
“No every piece of news on Earth” is not a technically honest guarantee. IQ200 uses a configurable source set and explicitly treats missing/unavailable sources as unverified. The Federal Reserve documents its RSS feeds as a distribution mechanism, and the SEC documents RSS feeds for current SEC materials/EDGAR updates.
