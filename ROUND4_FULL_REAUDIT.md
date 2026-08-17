# IQ200 Round 4 — Full Re-Audit & Fix Report

## Audit result

The uploaded Round-4 build was re-audited from the source tree rather than trusting its previous PASS claims.

### Verification performed
- Source tree inspected: 207 project files.
- Python `compileall`: PASS.
- Pytest excluding the known `aiosqlite` environment blocker: **38 passed**.
- Full pytest: **38 passed, 2 setup errors** because this execution environment does not have `aiosqlite` installed. The dependency is declared in `backend/requirements.txt`.
- Frontend build was not executed because `apps/web/node_modules` is not included in the ZIP.
- No plaintext real API keys were found in the source tree.

## Issues found and fixed in this round

1. **Cross-user idempotency collision**
   - `Trade.client_request_id` was globally unique, so two different users using the same request ID could collide.
   - Fixed at the model/repository layer to scope idempotency to `(user_id, client_request_id)`.
   - Note: existing production databases need a schema migration before this model change is deployed over an already-created database.

2. **Audit payload type bug**
   - Audit records were writing Python dictionaries into a SQL `Text` column.
   - Fixed by JSON-serializing audit payloads before persistence.

3. **Shared exchange credentials across authenticated users**
   - Execution previously used global `BINANCE_API_KEY/BINANCE_API_SECRET`, even though the application has user accounts and a credential-vault endpoint.
   - Fixed testnet and real Binance paths to load the authenticated user's encrypted credentials from the vault.
   - Shared environment credentials are now only accepted when `SINGLE_OPERATOR_MODE=true`.
   - OANDA credential loading was also routed through the user vault for real-account paths.

4. **Credential-vault endpoint was too permissive**
   - Fixed provider validation to accept only Binance/OANDA and require the expected credential fields.

5. **Unauthenticated real-provider status disclosure**
   - `/api/real/status` now requires authentication and reports credential availability for the logged-in user.

6. **Production JWT secret**
   - Production now refuses the insecure development fallback JWT secret.
   - `JWT_SECRET_KEY` must be supplied for production.

7. **Unsafe Docker database password**
   - `docker-compose.yml` no longer hardcodes `postgres` as the database password.
   - It requires `POSTGRES_PASSWORD` from `.env`.

8. **Invalid take-profit risk values**
   - Take-profit percentage is now bounded to 1–100% and resulting protection prices must remain positive.

## Remaining external validation blockers

These cannot honestly be marked PASS inside this offline audit:
- Binance Testnet network execution.
- Real Binance/OANDA execution.
- OpenAI API response validation with a real key.
- Telegram webhook delivery.
- PostgreSQL integration against the deployed database.
- Next.js production build.
- Historical-data certification and long-running worker behavior.

These are deployment/integration checks, not fabricated as unit-test PASS.

## API keys / secrets required

### Required for the basic app
- `JWT_SECRET_KEY` — application signing secret. Generate a strong random 32+ character value.
- `POSTGRES_PASSWORD` — PostgreSQL password if using Docker Compose.
- `CREDENTIAL_VAULT_KEY` — recommended dedicated Fernet key for encrypting broker credentials. If omitted, the project derives the vault key from `JWT_SECRET_KEY`.

### Required for AI analysis
- `AI_API_KEY` — OpenAI API key.
- `AI_MODEL` can remain `gpt-4o-mini` unless another supported model is configured.

### Required for Binance Testnet trading
- Binance Testnet API key
- Binance Testnet API secret

Store them through the authenticated `/api/security/credentials` endpoint. Do not put them in the frontend `.env.local`.

### Required only for live Binance
- Real Binance API key
- Real Binance API secret
- Live trading must remain OFF until external certification is complete.

### Required only for OANDA/FX
- OANDA API token
- OANDA account ID
- `OANDA_PRACTICE=true` for practice/sandbox.

### Optional
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_IDS`
- Custom `NEWS_FEEDS`

## Important safety setting

Keep:
- `LIVE_TRADING=false`
- `PAPER_TRADING=true` or testnet mode
- `ENABLE_WORKERS=false` until the testnet path has been verified.

For multi-user deployments, keep:
- `SINGLE_OPERATOR_MODE=false`

For a deliberately single-operator deployment using environment broker credentials, `SINGLE_OPERATOR_MODE=true` is allowed, but it should not be used when multiple accounts/users are expected.

## Deployment note

The database model changed. For a brand-new database, `init_db()` creates the correct schema. For an existing deployed database, run a proper migration that removes the old global unique constraint on `trades.client_request_id` and creates the composite unique constraint on `(user_id, client_request_id)` before deploying this build.
