# V0.5 Autopsy / Completion Map

Added in this build:
- AI provider abstraction + Chief Operator orchestration
- Fail-closed AI consensus
- News Engine normalization boundary
- PostgreSQL SQLAlchemy models
- Async database session
- Position repository
- Position monitoring worker skeleton
- Idempotency key utility
- Binance order-filter validation utilities
- Testnet execution service with risk gate
- Unified intelligence endpoint
- Startup DB initialization

Still required before production:
- Real AI provider credentials and prompt/evaluation harness
- Production news feeds + source trust/deduplication
- Full database migrations (Alembic)
- Auth/2FA/RBAC
- Persistent idempotency records
- WebSocket market/order streams
- Testnet order reconciliation and partial-fill state machine
- Automated SL/TP exit orders with safe cancellation/replacement
- Trailing-profit state machine
- Full portfolio/exposure risk engine
- Telegram/voice integration
- Security and load testing
- Observability/alerts/backups
- Legal/compliance review for intended jurisdiction
- Separate live adapter behind an explicit feature flag

Critical invariant:
LIVE_TRADING remains disabled. The system must fail closed whenever AI, market data,
news, exchange state, or risk state is stale/ambiguous.
