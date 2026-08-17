# Real-Time Market Intelligence

IQ200 now has a real read-only live monitoring layer for Binance spot markets.

## What it does
- Consumes Binance public `bookTicker` WebSocket data continuously for the configured watchlist.
- Refreshes technical analysis and relevant news on a slower cadence.
- Includes crypto feeds plus official Federal Reserve and SEC feeds for market-moving macro/regulatory events.
- Deduplicates/limits alerting and emits high/critical market-impact alerts.
- Exposes an authenticated status endpoint and an authenticated WebSocket stream.
- Never places orders from the real-time monitoring layer.

## Trading safety boundary
Monitoring can produce evidence and alerts. It cannot bypass the normal authenticated trading route, risk engine, TOTP, idempotency, confirmation, or kill switch.

## Limitations
No system can observe literally every piece of information published worldwide. The engine therefore uses a configurable source set and explicitly reports when data is unavailable. It must not claim that a trade is guaranteed to profit.

## Decision intelligence
The user-facing intelligence endpoint now builds one evidence package from live Binance technical candles, live public order-book depth, current news/impact, historical returns, regime detection, optional trained ML, and the multi-agent council. A critical market-moving news event forces the chief judge to `WAIT`.

The opportunity scanner no longer uses placeholder confidence/risk numbers; it consumes the same council evidence and remains non-executing.
