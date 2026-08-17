# IQ200 — Final Live-Money Gate

This build is code-audited for a controlled Binance Spot live test. It does **not** claim that exchange/network failures are impossible and it does not place an order automatically.

## Required before the human live test

- `APP_ENV=production`
- `BROKER=binance`
- `LIVE_TRADING=true`
- `PAPER_TRADING=false`
- `BINANCE_TESTNET=false`
- `ENABLE_WORKERS=true`
- `LIVE_TRADING_CONFIRM=I_UNDERSTAND_LIVE_TRADING`
- strong `JWT_SECRET_KEY`
- dedicated `CREDENTIAL_VAULT_KEY`
- user-specific Binance API credentials stored in the encrypted vault
- Binance API key has **withdrawals disabled**
- API key is restricted to the server IP when possible
- TOTP enabled for the trading user
- kill switch tested before the first live order

## What the live path does

1. Authenticates the user and requires TOTP.
2. Checks the user kill switch.
3. Reads live Binance account balances and live market data server-side.
4. Applies risk and Binance symbol filters.
5. Uses user-scoped idempotency.
6. Sends the live market order.
7. Reconciles unknown outcomes by exchange order ID **or client order ID** so a crash cannot silently justify a second submission.
8. Uses actual executed quantity/quote value for local accounting.
9. Installs Binance exchange-side OCO protection for a newly opened spot long.
10. If protection cannot be installed, it attempts an emergency flatten; failure freezes the account.
11. The position monitor checks the exchange-side OCO before considering a competing emergency exit.
12. Reconciliation and monitoring use live Binance when `LIVE_TRADING=true` and Testnet only when it is false.

## First live test

Use the smallest practical amount. Do not test with an amount whose loss would matter to you.

The first test should be a manually initiated BUY on a liquid symbol, followed by verification of:

- exchange order ID and actual fill
- local position quantity/entry price
- OCO exists on Binance
- stop-loss and take-profit prices are correct
- dashboard shows the position
- kill switch prevents another order
- restart/recovery does not create a duplicate

Do not increase size until those checks pass.
