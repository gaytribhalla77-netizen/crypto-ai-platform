# V0.3 status

Added:
- Fail-closed production-style risk validation
- Automatic opportunity amount ceiling
- 5% default stop-loss calculation
- 5% default take-profit calculation
- Position monitoring logic
- Basic AI consensus layer
- Dedicated trading risk API
- Health endpoint exposing safety mode

Still intentionally disabled:
- Real-money Binance order placement
- Autonomous live trading
- Production news provider
- Production AI provider credentials

Next production gate:
1. Binance testnet authenticated orders
2. Idempotency and duplicate-order tests
3. Partial-fill handling
4. WebSocket/order reconciliation
5. Persistent database
6. Authentication/2FA
7. Telegram confirmation flow
8. Full news pipeline
9. AI provider adapter
10. Security/stress audit
