# Binance Testnet

This build adds an authenticated Binance Spot Testnet adapter.

## Configuration

Set in `.env`:

BINANCE_TESTNET=true
BINANCE_API_KEY=your_testnet_key
BINANCE_API_SECRET=your_testnet_secret

Use **testnet credentials only**.

## Safety

- Live-money trading is not implemented.
- Never put secrets in frontend code.
- Never enable withdrawal permissions.
- The testnet order endpoint is intentionally low-level.
- Production execution still needs exchange-filter validation, quantity/precision handling, idempotency, reconciliation, partial-fill handling, and a kill switch.

## Testnet flow

1. Configure testnet credentials.
2. Call `/api/testnet/account`.
3. Validate symbol filters.
4. Calculate legal quantity.
5. Run a small testnet order.
6. Verify exchange order status.
7. Persist the order and audit event.
