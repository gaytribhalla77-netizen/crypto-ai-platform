import asyncio
import logging
import os
import sys

# workers/ lives at the repo root (a sibling of backend/), but
# docs/deployment/LOCAL_SETUP.md runs uvicorn from inside backend/, so only
# backend/ is on sys.path by default. Add the repo root too so `import
# workers...` resolves regardless of which directory the process was
# started from.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from api.news_routes import router as news_router
from api.dashboard_routes import router as dashboard_router
from api.voice_routes import router as voice_router
from api.ml_routes import router as ml_router
from api.intel_routes import router as intel_router
from api.trading_routes import router as trading_router
from api.testnet_routes import router as testnet_router
from api.v05_routes import router as v05_router
from api.v06_routes import router as v06_router
from api.v09_15_routes import router as v09_router
from api.advanced_routes import router as advanced_router
from api.security_routes import router as security_router
from api.real_routes import router as real_router
from api.realtime_routes import router as realtime_router
from auth.routes import router as auth_router
from database.session import init_db
from core.config import settings
from monitoring.health import health_registry

logger = logging.getLogger("main")

app = FastAPI(title="AI Crypto Trading Platform", version="1.6.0")

# The Next.js dashboard (apps/web) runs on a different origin in dev
# (localhost:3000 -> localhost:8000), so it needs CORS explicitly.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in [router, news_router, dashboard_router, voice_router, ml_router, intel_router, trading_router, testnet_router,
          v05_router, v06_router, v09_router, advanced_router, security_router, real_router, realtime_router, auth_router]:
    app.include_router(r)

_background_tasks: list[asyncio.Task] = []


@app.on_event("startup")
async def startup():
    await init_db()

    if settings.enable_workers:
        # Off by default (ENABLE_WORKERS=false) so tests and simple demo
        # runs don't unexpectedly spin up polling loops against public
        # APIs. Turn on explicitly once you've reviewed workers/*.
        from workers.health_monitor import HealthMonitorWorker
        from workers.market_scanner import market_scanner
        from workers.position_monitor import PositionMonitorWorker
        from workers.order_reconciliation import OrderReconciliationWorker
        from api.realtime_routes import _monitor as realtime_monitor

        health_worker = HealthMonitorWorker()
        position_worker = PositionMonitorWorker()
        reconciliation_worker = OrderReconciliationWorker()
        realtime_monitor_task = asyncio.create_task(realtime_monitor.start())

        _background_tasks.append(asyncio.create_task(health_worker.run_forever()))
        _background_tasks.append(asyncio.create_task(market_scanner.run_forever()))
        _background_tasks.append(asyncio.create_task(position_worker.run_forever()))
        _background_tasks.append(asyncio.create_task(reconciliation_worker.run_forever()))
        _background_tasks.append(realtime_monitor_task)
        logger.info("Background workers started: health_monitor, market_scanner, position_monitor, order_reconciliation")
    else:
        logger.info("ENABLE_WORKERS is false — no background monitoring is running.")


@app.on_event("shutdown")
async def shutdown():
    from api.realtime_routes import _monitor as realtime_monitor
    await realtime_monitor.stop()
    for t in _background_tasks:
        t.cancel()


@app.get("/health")
async def health():
    # Reflects what's actually true, not a hardcoded claim. "risk_manager"
    # used to always say "enabled" regardless of which (contradictory) risk
    # class a given route actually used — there is now exactly one
    # (trading.risk_manager.engine.RiskEngine).
    return {
        "status": "ok",
        "version": "1.6.0",
        "live_trading": settings.live_trading,
        "paper_trading": settings.paper_trading,
        "testnet": not settings.live_trading,
        "risk_engine": "single (RiskEngine: per-trade + portfolio)",
        "fail_closed": True,
        "workers_enabled": settings.enable_workers,
        "dependencies": health_registry.snapshot(),
    }
