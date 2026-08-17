# V0.6 — First 8 items implementation

Implemented as a development/testnet build:
1. AI Brain — provider abstraction + OpenAI-compatible structured JSON call, fail-closed fallback.
2. News Engine — configurable JSON feed boundary, normalization and safe empty fallback.
3. Database — SQLAlchemy async models/session/repositories for users, trades, positions and audit events.
4. Binance Testnet — signed account/order/status/exchange-info client.
5. Position/Risk — 5% default protection calculations and monitoring.
6. Authentication foundation — secure scrypt password hashing endpoint.
7. Telegram — architecture remains in the same backend and can be attached to these APIs.
8. Testnet execution — risk-gated order service with client order IDs.

IMPORTANT:
- Live trading is OFF.
- Testnet credentials must be used only.
- Production authentication still needs full sessions, email verification, 2FA, RBAC and rate limiting.
- News providers must be reviewed for licensing/reliability.
- AI outputs are advisory and never guaranteed.
