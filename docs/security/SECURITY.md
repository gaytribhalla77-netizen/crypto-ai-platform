# Security requirements

- Encrypt exchange secrets at rest.
- Never expose Binance API secret to the browser.
- Withdrawal permissions must be disabled.
- Use least-privilege API permissions.
- Add authentication and 2FA.
- Rate-limit command endpoints.
- Use idempotency keys for orders.
- Verify exchange order status after submission.
- Fail closed when market data is stale or AI health is degraded.
- Maintain audit logs.
