# Crypto AI Platform — Autopsy Fix Report

## Scope
This patch preserves the existing project and fixes the highest-risk issues identified during the autopsy. No live-trading adapter was introduced.

## Fixed

1. **Client-controlled portfolio risk values removed from canonical testnet order flow**
   - Balance, exposure, daily loss and open-position count are now derived server-side.
   - Added `PortfolioStateService` and a daily server-owned equity baseline.

2. **Raw exchange-order bypass disabled**
   - `POST /api/testnet/order` now fails closed with HTTP 410.
   - Orders must use the canonical `/api/v06/testnet/order` pipeline.

3. **Unified risk engine hardened**
   - BUY increases exposure; SELL exits no longer increase exposure.
   - Daily loss blocks new exposure but permits protective exits.
   - Max-position check applies to new BUY exposure.

4. **Stop-loss / take-profit monitor now executes protective testnet exits**
   - Exit orders use deterministic idempotency keys.
   - Unknown exchange outcomes remain UNKNOWN/open for reconciliation.
   - Position is marked closed only after a FILLED exchange response.

5. **Actual exchange fill price is used for new positions**
   - Weighted fill price and executed quantity are preferred over client-requested price/quantity when available.
   - SL/TP are recalculated from actual fill price.

6. **Authentication hardening**
   - Passwords are no longer sent in query strings.
   - Removed the public `/api/auth/password-hash` utility endpoint.
   - Added basic login failure throttling.
   - Frontend token storage moved from persistent `localStorage` to `sessionStorage` as a minimum-change security improvement.

7. **Unsafe legacy risk endpoint disabled**
   - `/api/v09-15/risk` now fails closed instead of accepting caller-supplied portfolio figures.

8. **Frontend fake portfolio values removed**
   - Trade form and voice trading no longer send fake `balance=10000`, `daily_loss_pct=0`, etc.

9. **Live trading remains explicitly disabled**
   - Startup refuses `LIVE_TRADING=true` because a separately audited live exchange adapter is not implemented in this build.

## Validation
- Python `compileall`: PASS.
- Risk-engine smoke checks: PASS.
- Existing pytest suite: **10 passed, 2 environment errors** because the audit runtime does not have `aiosqlite` installed. The project already declares `aiosqlite` in `backend/requirements.txt`; this is an execution-environment dependency issue, not a missing project dependency.
- Frontend build could not be executed from the extracted project root because there is no root `package.json`; the Next.js package is under `apps/web`.

## Still intentionally NOT claimed as complete
The following remain future work and were not falsely marked as fixed:

- Full multi-agent/adversarial trading council
- Regime detection engine
- Order-book intelligence
- Strategy backtesting with fills/slippage/fees
- Walk-forward/Monte-Carlo validation
- Model drift and strategy promotion gates
- Failure memory/self-learning loop
- Full portfolio correlation/VaR engine
- Institutional-grade event bus
- Fully audited live exchange adapter
- HttpOnly-cookie auth/CSRF architecture
- Native FX/forex broker adapter
