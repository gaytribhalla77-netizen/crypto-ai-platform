# API contracts

Planned endpoints:
- GET /health
- GET /api/market/{symbol}
- POST /api/trade/validate
- POST /api/trade/confirm
- GET /api/portfolio
- GET /api/positions
- GET /api/news
- GET /api/opportunities
- POST /api/telegram/webhook
- GET /api/system/health

All trade endpoints must authenticate, validate risk, and use idempotency.
