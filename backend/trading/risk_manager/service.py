"""DEPRECATED scaffold risk manager.

This used to always return allowed=False regardless of input, and lived
alongside two other independent risk checks (ProductionRiskManager,
PortfolioRisk) with no route guaranteed to use all three. That
contradiction was a critical audit finding: nothing enforced a single
risk authority.

Kept only so old imports don't break. It now delegates to
trading.risk_manager.engine.RiskEngine, which is the one class new code
should call directly. Do not add new logic here.
"""
from trading.risk_manager.engine import risk_engine


class RiskManager:
    def __init__(self):
        self._engine = risk_engine

    def validate(self, symbol: str, side: str, amount_usdt: float):
        # No entry price / portfolio context available at this call
        # signature, so this can only run the per-trade leg. Prefer
        # RiskEngine.validate() directly wherever portfolio context
        # (balance, exposure, open positions) is available.
        decision = self._engine.per_trade.validate(side, amount_usdt, entry_price=1.0, automatic=False)
        if not decision.allowed:
            return {"allowed": False, "reason": decision.reason}
        return {
            "allowed": False,
            "reason": "This endpoint cannot evaluate portfolio-level risk. "
                       "Use /api/trading/risk-check (RiskEngine) for a real trade decision.",
        }
