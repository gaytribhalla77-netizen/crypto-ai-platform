# Next step: Binance Spot Testnet smoke test

This is intentionally a **testnet-only** procedure. Do not put live Binance credentials into this environment.

## 1. Install dependencies

```bash
pip install -r requirements-dev.txt
```

The audit runner used for this package does not have network/package installation access, so its two SQLite idempotency tests are blocked until `aiosqlite` is installed. The project already declares `aiosqlite`.

## 2. Configure testnet credentials locally

Copy `.env.example` to `.env` and set:

- `LIVE_TRADING=false`
- `PAPER_TRADING=true`
- `BINANCE_TESTNET=true`
- `BINANCE_API_KEY=<Binance Spot Testnet key>`
- `BINANCE_API_SECRET=<Binance Spot Testnet secret>`

Never paste secrets into chat or commit `.env`.

## 3. Read-only connectivity smoke test

From the repository root:

```bash
python scripts/testnet_smoke.py
```

Expected:

- testnet account authenticated
- requested symbol exists
- **no order is sent**

## 4. One controlled testnet BUY

Only after the read-only check succeeds:

```bash
python scripts/testnet_smoke.py --symbol BTCUSDT --quantity 0.00001 --place-order
```

The command sends exactly one testnet MARKET BUY. It does not use live endpoints.

## 5. Application-level test

Start the backend with `LIVE_TRADING=false` and `ENABLE_WORKERS=true`. Then use the authenticated `/api/v06/testnet/order` path so risk checks, exchange filters, idempotency, persistence and exchange-side protection are exercised together.

## 6. Required evidence before live mode

Record:

1. successful testnet account authentication;
2. successful testnet order ID and fill;
3. successful exchange-side OCO protection placement;
4. stop-loss trigger test;
5. take-profit trigger test;
6. duplicate request test;
7. unknown-outcome/reconciliation test;
8. application restart with an open position;
9. kill-switch test;
10. worker recovery test.

Only after all ten are successful should live-money certification be considered.
