# IQ200 REAL DEPLOYMENT GATE

This repository is intentionally real-provider-only in production paths.

## Before enabling live execution

- Install `backend/requirements.txt` including `aiosqlite` for the default local database.
- Set a strong `JWT_SECRET_KEY`.
- Configure `AI_API_KEY` for the real AI provider.
- Choose exactly one broker with `BROKER=binance` or `BROKER=oanda`.
- Configure only the corresponding broker credentials on the server.
- Never expose broker credentials to the Next.js client.
- Enable and verify user TOTP 2FA.
- Keep `LIVE_TRADING=false` until the account/broker sandbox has been exercised end-to-end.
- When and only when the operator accepts real-money execution risk, set `LIVE_TRADING=true` and `LIVE_TRADING_CONFIRM=I_UNDERSTAND_LIVE_TRADING`.
- Keep the kill switch available and test reconciliation before any autonomous execution.

## What is not claimed

This build does not claim a profitable strategy, guaranteed win rate, or institutional/HFT execution quality. Real provider connectivity is implemented; trading performance still has to be demonstrated by live provider data, paper/sandbox validation, walk-forward testing, and controlled deployment.
