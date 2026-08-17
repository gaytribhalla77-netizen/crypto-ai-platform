# IQ200 — Static Audit Round 1 + Fixes Applied

STATUS: bugs #1-#5 below are now FIXED, with regression tests that
actually run (pure stdlib, no third-party install needed) and pass. See
"Fixes applied" section at the bottom for exactly what changed and why.
Bug #6 (cosmetic duplicate line) is also fixed. Nothing below was silently
converted from UNVERIFIED to PASS -- see the still-BLOCKED section.

Environment constraints: no PyPI/npm registry access (403), no browser, no
broker sandbox credentials, no running Postgres/Redis. Everything below is
either (a) verified via static analysis actually executed against this repo,
or (b) explicitly marked BLOCKED/UNVERIFIED — nothing here is guessed.

## Confirmed real bugs (not yet fixed)

1. **HIGH — Frontend env var mismatch.**
   `apps/web/app/page.tsx` reads `process.env.NEXT_PUBLIC_API_URL`.
   `apps/web/app/lib/api.ts` and `.env.local.example` both use
   `NEXT_PUBLIC_API_BASE`. `NEXT_PUBLIC_API_URL` is set nowhere in the repo.
   Effect: the entire main dashboard (Command/Market/Council/Twin/Memory/
   Lab/Execution/Audit tabs in page.tsx) silently falls back to
   `http://localhost:8000` in every deployed environment.

2. **HIGH — Unauthenticated write into shared AI memory store.**
   `POST /api/advanced/memory/add` (backend/api/advanced_routes.py) has no
   `Depends(get_current_user)` and no rate limit. It appends directly to a
   single global, unbounded `data/market_memory.jsonl`
   (backend/memory/market_memory.py) with no per-user scoping. Anyone can
   inject fabricated memory records that `MarketMemory.similar()`/`digest()`
   later feed back into the AI decision pipeline — a data-poisoning vector
   — plus unbounded disk growth.

3. **MEDIUM-HIGH — No rate limiting outside login.**
   `_check_rate_limit` exists only in backend/auth/routes.py. All 22
   endpoints in advanced_routes.py (Monte Carlo up to 10,000 sims,
   walk-forward, self-learning, research/validate, etc.) are both
   unauthenticated and unthrottled — OWASP API4 resource-exhaustion
   exposure once internet-facing.

4. **MEDIUM — `/api/advanced/providers/status` unauthenticated.**
   Reveals whether broker API keys are configured and whether live trading
   is enabled, to any anonymous caller.

5. **LOW — Dead dependencies.**
   `redis`, `python-dotenv`, `pydantic-settings` are declared in
   requirements.txt but never imported anywhere in the Python code.
   `redis` is also provisioned as a running service in docker-compose.yml
   that the backend never actually connects to (config uses a plain
   dataclass with os.getenv, not pydantic-settings; .env loading relies on
   the process environment, not python-dotenv).

6. **COSMETIC — `apps/web/.env.local.example`** sets
   `NEXT_PUBLIC_API_BASE` twice (duplicate line).

## Verified as correct (real PASS)

- All 145 .py files compile cleanly (py_compile), zero syntax errors.
- Every `api.X()` call used in React components resolves to a real method
  in lib/api.ts, and every path in lib/api.ts resolves to a real backend
  route once each router's own `prefix=` is accounted for. No dead
  frontend-to-backend calls found.
- No hardcoded secrets in source; .env.example ships all-empty values.
- core/config.py fails closed: raises RuntimeError at import time if
  LIVE_TRADING=true with the dev-default JWT secret, missing broker
  credentials, or a missing/incorrect LIVE_TRADING_CONFIRM value.
- TradeRepository.create_idempotent enforces client_request_id uniqueness
  at the DB constraint level (not just in-process), explicitly to survive
  a race between two concurrent identical order requests.
- No mock/fake/simulated data disguised as real in production code paths.

## Retracted (checked, was wrong)

- Initially suspected /health and /analyze/{symbol} were double-registered
  and shadowing each other across route files. Rechecked: every router
  declares its own `prefix=` in APIRouter(), so the full paths are
  distinct. No collision. Logged here so the correction isn't lost.

## BLOCKED / UNVERIFIED (per project rule: never converted to PASS)

- Clean `pip install` / `npm ci` / `npm run build` — registry access
  returns 403 in this sandbox.
- Real browser click-through of all 8 UI modules, mobile/tablet checks.
- pytest execution — dependencies not installable here.
- Broker sandbox execution, DB restart/failover, concurrency/load testing
  — no live Postgres/Redis/broker credentials in this environment.

## Fixes applied (round 1 + follow-up hardening)

1. **Frontend env var mismatch** — `apps/web/app/page.tsx` now reads
   `NEXT_PUBLIC_API_BASE` (was `NEXT_PUBLIC_API_URL`), matching `lib/api.ts`
   and `.env.local.example`.
   Regression test: `tests/regression/test_frontend_env_var_fix.py` — PASS.

2. **Memory isolation + authenticated access** — both `POST /api/advanced/memory/add`
   and `POST /api/advanced/memory/similar` require `Depends(get_current_user)`.
   `MarketMemory` is now bound to a positive authenticated `user_id` and stores
   only in `data/market_memory/users/<user_id>.jsonl`; it never reads the old
   shared `data/market_memory.jsonl`. Per-record (64 KiB) and per-user (10 MiB)
   limits prevent the old unbounded-disk-growth problem. A user's similarity
   query therefore cannot read another user's records.
   Regression test: `tests/regression_round2_stdlib.py::test_memory_isolation` and
   `::test_api_memory_routes_are_authenticated_and_user_scoped` — PASS.

3. **No rate limiting on advanced_routes.py** — added
   `backend/core/rate_limit.py`, a small dependency-free sliding-window
   per-IP limiter (30 calls / 60s), applied at the router level so it
   covers all 22 routes in one change. This is explicitly an in-process
   backstop, not a distributed limiter — will need replacing if this ever
   runs as more than one process.
   Regression test: `...::test_router_has_rate_limit_dependency` — PASS.

4. **Unauthenticated provider status** — `GET /api/advanced/providers/status`
   now requires `Depends(get_current_user)`.
   Regression test: `...::test_providers_status_requires_auth` — PASS.

5. **Dead dependencies + unused Redis infrastructure** — removed `redis`,
   `python-dotenv`, and `pydantic-settings` from `backend/requirements.txt` and
   removed the unused `redis` service plus backend `depends_on` entry from
   `docker-compose.yml`. A repo-wide AST scan and Round 2 regression test verify
   there are no live Redis Python imports or compose dependency references.
   Regression test: `tests/regression/test_no_dead_dependencies.py` plus
   `tests/regression_round2_stdlib.py::test_no_live_redis_dependency` — PASS
   (re-derives unused-ness from the actual source tree every run, so it
   catches a future re-add of the dependency without a real use, or a
   future real use without re-declaring it).

6. **Duplicate env line** — removed the duplicate `NEXT_PUBLIC_API_BASE=`
   line in `apps/web/.env.local.example`.

Round 2 follow-up verification (real, executed evidence):
- `tests/regression_round2_stdlib.py`: 4/4 PASS using only Python stdlib.
- `python3 -m compileall -q backend`: PASS.
- Repo-wide Redis import scan: PASS (no Python Redis imports).
- Compose scan: PASS (no Redis service/dependency).
- Requirements scan: PASS (no Redis dependency).
- The old shared memory file is not read by the new `MarketMemory` implementation.

Verified after fixes (real, executed evidence):
- All `.py` files in the repo, including the 3 new regression test files
  and the new `core/rate_limit.py`, still compile cleanly (`py_compile`,
  0 errors).
- All 3 regression test files run standalone with plain `python3` (no
  install needed) and pass.
- Re-ran the mock/fake/placeholder grep against the changed files —
  nothing new introduced; the only hits are the same pre-existing
  legitimate ones (Monte Carlo `simulate()`, a disclaiming docstring).
- Import of `core.rate_limit` and `auth.dependencies` in
  `advanced_routes.py` resolve to real files at the paths FastAPI would
  actually import from (backend/ is the app root).

What these regression tests are (and are not): they're source-level static
checks (ast/text-based), not live HTTP requests through a running FastAPI
TestClient, because installing fastapi/pydantic/etc. is still blocked in
this environment (PyPI returns 403 here). They will catch someone silently
removing the auth dependency or the rate limiter in a future edit, but
they do NOT prove the endpoints behave correctly at runtime (e.g. that a
401 is actually returned, that the 429 status fires under real load). A
real `TestClient`-based test suite should replace/supplement these once
dependencies are installable.

## Not yet done at all

- No code fixes have been applied yet — this round was audit-only.
- Phases not yet touched: full AI decision-pipeline trace (brain.py through
  risk engine), self-learning loop validation, order-book intelligence,
  macro intelligence, backtest leakage checks, execution engine
  idempotency deep-dive beyond TradeRepository, database migration/
  transaction testing, full OWASP red-team pass beyond the auth-coverage
  spot check, performance/N+1 query analysis, test-suite content review
  (do the existing tests actually assert what they claim to).

## Round 3 — fixes to what Round 2 missed

Round 2 correctly fixed per-user memory scoping and removed Redis, but its
own regression suite (regression_round2_stdlib.py) only covered its own
new file — it never ran the pre-existing test suite, so it missed that it
broke `tests/test_iq200_seven_layers.py::test_memory_similarity`, which
still called the old `MarketMemory(path_str)` constructor. Confirmed by
actually executing that exact call against the new code:

    ValueError: user_id must be a positive integer

Fixed in this round:

1. `tests/test_iq200_seven_layers.py::test_memory_similarity` — updated to
   the new `MarketMemory(user_id)` API, using the same "swap BASE_DIR to a
   tmp dir for the test" pattern already used in
   regression_round2_stdlib.py::test_memory_isolation, so it writes to a
   throwaway directory instead of the real data/market_memory/users/.
   Verified by manually executing the exact fixed test body (pytest
   itself still isn't installable in this environment — PyPI returns 403)
   — it now passes.

2. `README.md` — removed "Redis" from the feature-list line describing the
   Docker scaffold (Redis was removed from docker-compose.yml in Round 2,
   this line was never updated).

3. `.env.example` — removed the orphaned `REDIS_URL=` line (confirmed by
   grep that no `.py` file reads `REDIS_URL` anywhere).

Full re-verification after these fixes:
- All 150 `.py` files, including the edited test file, compile clean.
- All 4 of Round 2's regression tests still pass.
- All 3 of Round 1's regression tests still pass.
- Fresh repo-wide scan: no redis imports, no hardcoded secrets, no new
  mock/fake markers introduced.
- Grepped for any other test file referencing MarketMemory/market_memory —
  only the one file existed, now fixed; no other pre-existing test was
  using the old constructor.

Residual, not fixed (flagging rather than silently expanding scope):
- `docs/trading/V1_7_DASHBOARD.md` line 114 still mentions Redis in a
  historical note ("the full original setup (DB, Redis, Docker) — nothing
  there changed"). Low value, deep in docs/, wasn't part of what was
  agreed to fix this round — left as-is.

## Round 4 — fixed the last residual doc mention

`docs/trading/V1_7_DASHBOARD.md` line 114 was updated to drop "Redis" from
"the full original setup (DB, Redis, Docker)". Confirmed by a fresh,
repo-wide, case-insensitive Redis grep across every .py/.yml/.md/.example/
.txt/.json/.ts/.tsx file: the only remaining hits are inside this audit
report, test assertions that check FOR the absence of Redis, and one
design-note comment in rate_limit.py explaining a hypothetical future
Redis-backed limiter — no stale operational docs left pointing at a
scaffold that no longer exists.

Re-verified after this fix: 150/150 files compile, all 4 Round 2 tests
PASS, all 3 Round 1 tests PASS.
