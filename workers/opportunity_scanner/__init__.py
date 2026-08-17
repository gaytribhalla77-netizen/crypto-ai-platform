"""Opportunity-scanner worker.

Previously an empty file. Ranks watchlist symbols using OpportunityEngine
against the latest market_scanner readings and surfaces candidates above a
score threshold, respecting the AUTO_OPPORTUNITY_MAX_USDT hard ceiling from
config.

Deliberately does NOT auto-execute trades. Wiring this straight into order
placement would bypass the confirmation flow the risk spec calls for
(manual trades ask for user confirmation; even "automatic opportunity"
trades are supposed to pass through the same risk engine + idempotency +
audit path as everything else, which this worker does not implement).
Candidates are only queued as notifications for a human/approval step to
act on.
"""
import asyncio
import logging

from opportunity.engine import OpportunityEngine
from core.config import settings
from workers.market_scanner import market_scanner
from intelligence.council_service import build_council

logger = logging.getLogger("workers.opportunity_scanner")


class OpportunityScannerWorker:
    def __init__(self, score_threshold: float = 70.0, interval_seconds: int = 30, notifier=None):
        self.engine = OpportunityEngine(settings.auto_opportunity_max_usdt)
        self.score_threshold = score_threshold
        self.interval_seconds = interval_seconds
        self.notifier = notifier  # optional NotificationWorker instance

    async def run_once(self):
        if not settings.auto_opportunity_enabled:
            return []
        candidates = []
        for symbol in market_scanner.latest:
            try:
                evidence = await build_council(symbol)
            except Exception:
                logger.exception("council evidence unavailable for %s", symbol)
                continue
            council = evidence.get("council", {})
            if council.get("veto") or council.get("chief_judge", {}).get("action") == "WAIT":
                continue
            confidence = float(council.get("chief_judge", {}).get("confidence", 0))
            action = council.get("chief_judge", {}).get("action")
            risk_score = 100.0 - confidence
            momentum = float(evidence.get("technical", {}).get("change_20_candles_pct", 0))
            opp = self.engine.rank(symbol, confidence, risk_score, momentum)
            if opp.score >= self.score_threshold and action in {"BUY", "SELL"}:
                candidates.append(opp)
                if self.notifier:
                    await self.notifier.enqueue(
                        "opportunity_detected", "MEDIUM",
                        {"symbol": opp.symbol, "score": opp.score, "suggested_amount_usdt": opp.suggested_amount_usdt, "action": action, "council_confidence": confidence},
                    )
        return candidates

    async def run_forever(self):
        while True:
            try:
                await self.run_once()
            except Exception:
                logger.exception("opportunity_scanner tick failed")
            await asyncio.sleep(self.interval_seconds)
