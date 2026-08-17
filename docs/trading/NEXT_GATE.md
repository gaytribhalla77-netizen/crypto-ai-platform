# Next gate after Testnet

Before any live-money feature:
- Complete symbol exchange-filter service.
- Add idempotency keys.
- Add order-state reconciliation.
- Handle partial fills/cancellations.
- Persist orders/positions in PostgreSQL.
- Add authentication and 2FA.
- Add encrypted API credentials.
- Add emergency kill switch.
- Add websocket market/order streams.
- Add comprehensive integration and failure tests.
- Security review.
- Only then design a separately gated live adapter.
