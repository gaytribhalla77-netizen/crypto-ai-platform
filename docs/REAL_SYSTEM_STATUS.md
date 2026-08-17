# REAL SYSTEM STATUS — IQ200

This build removes simulated AI/execution fallbacks from the production path.

## Real integrations

- Binance Spot REST: public market data + signed account/order endpoints.
- OANDA v20: real FX pricing, candles, account summary, positions, and order execution.
- OpenAI: real provider only; if the key is absent, the AI returns `NO_TRADE/not_configured` rather than fabricating an answer.

## Safety gates

Live execution requires all of:

1. `LIVE_TRADING=true`
2. `LIVE_TRADING_CONFIRM=I_UNDERSTAND_LIVE_TRADING`
3. Real broker credentials
4. Enabled per-user TOTP 2FA
5. Per-user kill switch not enabled
6. Broker configured consistently with `BROKER`

The default is live trading **off**.

## No fake data in production

The previous mock AI provider and FX sandbox endpoint have been removed from the backend production graph. Testnet remains an actual exchange test environment, not a fabricated price simulator.

## Important

Real credentials must be supplied by the operator. This archive does not contain or invent credentials. Never put broker secrets in the Next.js browser environment.
