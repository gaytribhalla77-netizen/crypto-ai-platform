# Production Readiness — Autopsy items 7–12

This document records the hardening added after the deeper Autopsy audit. It is intentionally conservative: live trading remains disabled by default and external credentials are never invented.

## 7. Notifications and integrations
- Added `backend/notifications.py` with Telegram and generic webhook adapters.
- Missing credentials fail closed and do not break the application.
- Telegram recipients are restricted by `TELEGRAM_ALLOWED_USER_IDS`.
- Notification network calls use bounded timeouts.

## 8. Error handling and observability
- Added request IDs and latency headers through `RequestObservabilityMiddleware`.
- Unhandled request exceptions are logged with request ID, method, path, and latency without logging secrets or request bodies.
- `/health` now reports uptime and shared component health.
- Database startup failures mark health as degraded and prevent unsafe startup.

## 9. Production environment validation
Run:

```bash
python scripts/validate_env.py
```

Production requires a strong `JWT_SECRET_KEY`. Live trading additionally requires the existing explicit confirmation gate, enabled workers, and a supported broker. The repository never stores real credentials.

## 10. Dependency reproducibility
- Backend dependency declarations remain centralized in `backend/requirements.txt`.
- CI installs dependencies from that single source and runs the complete test/build/security pipeline.
- Dependency drift is detected through CI dependency-audit jobs. Do not silently upgrade production dependencies outside a reviewed change.
- Frontend dependencies must be committed with a generated `package-lock.json` before a production deployment; the current repository intentionally avoids claiming a lock file that has not been generated and reviewed.

## 11. Documentation synchronization
The README, `.env.example`, local setup documentation, real-system status, and this readiness record now describe the same safety defaults: paper/testnet first, live off by default, credentials supplied by the operator, and fail-closed behavior when providers are unavailable.

## 12. Load and resilience testing
- Added an in-process concurrent load smoke test that sends 100 simultaneous `/health` requests.
- Added fail-closed notification and environment validation tests.
- Existing CI compiles the backend, runs pytest, builds the web application, runs E2E checks, and performs dependency/security validation.

### Certification rule
A passing code change is not itself a production certification. The final certification must be based on the single combined CI/E2E/PostgreSQL/security/load run requested by the operator, with all jobs green. Real-money execution is not part of that certification.
