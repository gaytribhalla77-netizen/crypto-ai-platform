import asyncio
import logging
import os
import sys
import time

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
from api.web_audit_routes import router as web_audit_router
from api.real_routes import router as real_router
from api.realtime_routes import router as realtime_router
from api.clawtrade_routes import router as clawtrade_router
from api.notification_routes import router as notification_router
from api.strategy_routes import router as strategy_router
from auth.routes import router as auth_router
from database.session import init_db
from core.config import settings
from monitoring.health import health_registry
from monitoring.http import RequestObservabilityMiddleware

logger = logging.getLogger("main")
app = FastAPI(title="AI Crypto Trading Platform", version="1.6.0")

app.add_middleware(RequestObservabilityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

for r in [router, news_router, dashboard_router, voice_router, ml_router, intel_router, trading_router, testnet_router,
          v05_router, v06_router, v09_router, advanced_router, security_router, web_audit_router, real_router, realtime_router,
          clawtrade_router, notification_router, strategy_router, auth_router]:
    app.include_router(r)

_background_tasks: list[asyncio.Task] = []
_started_at = time.monotonic()


@app.on_event("startup")
async def startup():
    health_registry.set("database", "ok", "initializing")
    try:
        await init_db()
        health_registry.set("database", "ok", "initialized")
    except Exception as exc:
        health_registry.set("database", "error", type(exc).__name__)
        raise

    health_registry.set("api", "ok", "startup complete")
    health_registry.set("workers", "ok" if settings.enable_workers else "disabled", "configured")

    if settings.enable_workers:
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
    snapshot = health_registry.snapshot()
    return {
        "status": "ok" if snapshot["status"] != "error" else "degraded",
        "version": "1.6.0",
        "uptime_seconds": round(time.monotonic() - _started_at, 2),
        "live_trading": settings.live_trading,
        "paper_trading": settings.paper_trading,
        "testnet": not settings.live_trading,
        "risk_engine": "single (RiskEngine: per-trade + portfolio)",
        "fail_closed": True,
        "workers_enabled": settings.enable_workers,
        "clawtrade_enabled": settings.clawtrade_enabled,
        "dependencies": snapshot,
    }
