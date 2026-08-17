# IQ200 — Final Code Audit Before Controlled Live Test

Date: 2026-08-17

## Decision

**READY FOR A HUMAN-CONTROLLED, SMALL-SIZE LIVE TEST — not a guarantee of profitability or immunity to exchange/network failure.**

The application is intentionally shipped with live trading **off by default**. The human operator must deliberately configure the production gates and supply their own Binance credentials. No real API secret is included in this archive.

## Final audit results

- Full pytest collection: **49 tests total**
- **47 passed**
- **2 blocked by the audit environment only**: both SQLite idempotency tests require the declared `aiosqlite` package, which is unavailable in this execution environment.
- All other test files: **47/47 passed**
- Python `compileall`: **PASS**
- Live safety suite: **PASS**
- Adapter/security regression suite: **PASS**
- Secret-pattern scan: **PASS**
- Non-destructive live preflight with valid temporary credentials: **PASS**

`aiosqlite` is already declared in `backend/requirements.txt` and `requirements-dev.txt`. It could not be downloaded in this environment because outbound package-network access is unavailable. The two blocked tests are therefore not reported as passing.

## Live-path fixes included

1. Live Binance uses the live REST base only when `testnet=False`.
2. Testnet and live portfolio state now use the same Binance adapter with an environment-selected endpoint.
3. The live security reconciliation endpoint no longer hard-codes Binance Testnet.
4. The background health monitor probes the configured Binance endpoint and reports `binance_live` in live mode.
5. Live order reconciliation can recover an order accepted by Binance even if the process crashed before persisting `orderId`, by querying the immutable client order ID.
6. Live position monitoring checks the exchange-side OCO state before considering a competing market exit.
7. If OCO status cannot be read, the monitor refuses to issue a competing market order and leaves the position for reconciliation.
8. The position monitor's Testnet trade service is only imported/executed in the explicit non-live branch.
9. Existing live order risk gates remain active: TOTP, kill switch, server-observed balance/equity, daily-loss baseline, exposure, open-position limit, symbol filters, precision, and notional checks.
10. Live BUYs use actual execution quantity/quote value and install Binance exchange-side OCO protection; protection failure attempts an emergency flatten and freezes the account if flattening fails.
11. Live SELL is reduce-only against a tracked application position.
12. User-scoped idempotency remains database-backed.
13. Production refuses the insecure JWT development secret.
14. Live mode requires workers and an explicit human confirmation string.

## Deliberate external-test boundary

The code cannot prove the following without a real Binance account and network path:

- actual live order acceptance/fill
- actual OCO creation and trigger behavior on Binance
- real-world network timeout/retry behavior
- actual exchange-side partial-fill behavior under live market conditions
- server restart/recovery against a real account

These must be exercised by the operator using the smallest practical amount.

## Do not do

- Do not paste API keys into chat.
- Do not enable withdrawals on the Binance API key.
- Do not start with a large balance/order.
- Do not use `BINANCE_TESTNET=true` for the live test.
- Do not set `PAPER_TRADING=true` in production live mode.

## First live test

Use `docs/LIVE_FINAL_CHECKLIST.md` and run `scripts/live_preflight.py` first. The preflight never places an order.

After the human-controlled test, the exchange response, order/OCO identifiers, and application logs can be audited for any remaining operational issue.
