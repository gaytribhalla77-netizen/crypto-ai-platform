# v1.6 — Fix pass on the v1.5 (points 9–15) audit

This build applies fixes for every CRITICAL and most HIGH issues found in
the independent autopsy of v1.5. It does **not** claim the platform is
production-ready — see "Still not done" below.

## Fixed

1. **Crash bug**: `/api/testnet/order` and `execution/testnet_service.py`
   called `client.place_test_order()`, which didn't exist on
   `BinanceTestnetClient`. Fixed to call `.order()`.
2. **Second crash bug found while fixing #1**: `ai/news/service.py` and
   `ai/risk/service.py` were plain sync functions passed into
   `asyncio.gather()` inside the orchestrator — this raises `TypeError` at
   runtime. Both are now `async def`.
3. **Idempotency is now real, not decorative.** `Trade.client_request_id`
   is a unique, indexed DB column. `TradeRepository.create_idempotent()`
   checks for an existing row first, and catches `IntegrityError` as a
   backstop against a race between the check and the commit. A duplicate
   request returns the existing trade's status instead of creating a
   second one and instead of resubmitting to the exchange.
4. **One risk authority instead of three.** `trading/risk_manager/engine.py`
   introduces `RiskEngine`, which runs the per-trade check
   (`ProductionRiskManager`) and the portfolio check (`PortfolioRisk`) and
   fails closed if either disallows. The old `RiskManager` class (which
   always returned `allowed: False`) is now a deprecated shim that
   delegates to `RiskEngine`. Every trading route now imports `RiskEngine`
   — verify with `grep -rn "RiskEngine\|risk_engine" backend/api/`.
5. **Auth exists.** `POST /api/auth/register` and `/login` issue short-lived
   JWTs (HS256, `JWT_SECRET_KEY` env var). `auth/dependencies.py::get_current_user`
   is now a dependency on every trading-capable route
   (`/api/trading/risk-check`, `/api/testnet/*`, `/api/v06/testnet/order`,
   `/api/v09-15/paper/order`). Market-data-only GETs remain public.
   The app refuses to start with `LIVE_TRADING=true` and the default dev
   JWT secret (see `core/config.py`).
6. **Telegram bot fails closed.** `TelegramCommandCenter` now checks
   `user_id` against `TELEGRAM_ALLOWED_USER_IDS` (comma-separated env var,
   empty by default — which means *deny everyone* until configured, not
   allow everyone).
7. **Exchange-filter validation is wired in, not dead code.**
   `trading/testnet_service.py::TestnetTradeService.execute()` fetches
   `exchangeInfo`, parses `LOT_SIZE`/`MIN_NOTIONAL`, and calls
   `validate_order_filters()` before ever calling `.order()`.
8. **Workers are implemented, not empty files**: `position_monitor`,
   `health_monitor`, `market_scanner`, `news_monitor` (with URL-based
   dedup), `notification_worker` (queue + priority filter), and
   `opportunity_scanner`. `main.py` starts `health_monitor`,
   `market_scanner`, and `position_monitor` on boot **only if
   `ENABLE_WORKERS=true`** — off by default so tests and simple demo runs
   don't unexpectedly start polling loops.
9. **The fake test is gone.** `tests/trading/test_testnet_safety.py` used
   to be `assert True`. It now asserts the live `ExecutionEngine` actually
   raises, and that filter validation actually rejects bad orders. Added
   `test_idempotency.py` and `test_risk_engine.py`.

## Verified by actually running (not just reading)

This sandbox has no network access, so `fastapi`/`sqlalchemy`/`pytest`
could not be installed to run the full suite. What *was* executed
directly:
- Every `.py` file compiles (`python3 -m py_compile`) — zero syntax errors.
- `RiskEngine.validate()` — ran all three branches (per-trade block,
  portfolio block, combined pass with correct stop-loss/take-profit math)
  directly in a script; all passed.
- `validate_order_filters()` — ran the below-min-notional,
  bad-step-precision, and valid-order cases directly; all passed.

Everything involving FastAPI routing or the async DB session layer was
carefully traced by hand (import graph, method signatures, dependency
wiring) but **not executed**. Before deploying: `pip install -r
backend/requirements-dev.txt` (or `requirements-dev.txt` at repo root) and
run `pytest`, then exercise the routes with a real HTTP client against a
live Postgres/SQLite instance.

## Still not done — do not treat this as production-ready

- **AI consensus/calibration (spec points 3–6)**: still a 2-signal weighted
  sum with no confidence-vs-outcome tracking. Not touched in this pass.
- **News reliability/freshness scoring (points 7–8)**: `NewsEngine` still
  returns `impact: UNASSESSED` unconditionally. The new `news_monitor`
  worker only adds scheduling and URL dedup — it does not add sentiment,
  source-trust, or freshness logic.
- **Live Binance execution**: `exchanges/binance/client.py` remains
  100% `NotImplementedError`. Only testnet has a real client.
- **Automatic opportunity execution**: `opportunity_scanner` ranks and
  queues candidates as notifications; it does not place trades. Wiring it
  to auto-execute would need its own risk-engine + idempotency + audit
  integration and a deliberate decision to enable `AUTO_OPPORTUNITY_ENABLED`.
- **Notification delivery**: `notification_worker` filters and logs; there
  is still no real Telegram/email/SMS channel wired up.
- **Order state machine**: `Trade.status` is closer to the spec now
  (`PENDING`/`SUBMITTED`/`UNKNOWN`/etc. are written by
  `TestnetTradeService`), but it's still a free-text column, not a DB
  enum, and there's no separate reconciliation job that resolves `UNKNOWN`
  trades against the exchange — that has to be a follow-up.
- **Rate limiting, CSRF, RBAC on admin actions**: none of this exists yet.
  `require_admin` dependency was added but nothing uses it — there is no
  admin route.
- **Chaos/load testing (points 26–27)**: not attempted.
- **Legal/compliance review (point 30)**: out of scope for a code fix pass
  by definition — needs a human, in your jurisdiction.

**Net effect on the autopsy scorecard**: the 8 CRITICAL findings from the
v1.5 autopsy are addressed. Security, Database, and Reliability move up
meaningfully (auth + idempotency + working workers). AI and News are
essentially unchanged — those need real design work, not a fix pass, and
claiming otherwise would repeat the exact failure mode your own master
prompt warns against (declaring "complete" without evidence).
