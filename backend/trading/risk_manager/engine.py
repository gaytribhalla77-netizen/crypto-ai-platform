"""Single authoritative, fail-closed risk engine."""
from dataclasses import dataclass
from trading.risk_manager.production import ProductionRiskManager, RiskDecision
from portfolio.risk import PortfolioRisk
from core.config import settings

@dataclass
class CombinedRiskDecision:
    allowed: bool
    reason: str
    stop_loss_price: float | None = None
    take_profit_price: float | None = None

class RiskEngine:
    def __init__(self, per_trade=None, portfolio=None):
        self.per_trade = per_trade or ProductionRiskManager(
            stop_loss_pct=settings.stop_loss_percent,
            take_profit_pct=settings.take_profit_percent,
            max_auto_usdt=settings.auto_opportunity_max_usdt,
        )
        self.portfolio = portfolio or PortfolioRisk()

    def validate(self, *, side: str, amount_usdt: float, entry_price: float,
                 balance: float, exposure: float, daily_loss_pct: float,
                 open_positions: int, automatic: bool = False,
                 stop_loss_pct: float | None = None,
                 take_profit_pct: float | None = None,
                 reduce_only: bool = False) -> CombinedRiskDecision:
        side = side.upper()
        if side not in {"BUY", "SELL"}:
            return CombinedRiskDecision(False, "Invalid order side.")
        if reduce_only and side != "SELL":
            return CombinedRiskDecision(False, "Reduce-only orders must be SELL orders in spot mode.")

        trade_decision: RiskDecision = self.per_trade.validate(
            side, amount_usdt, entry_price, automatic,
            stop_loss_pct=stop_loss_pct, take_profit_pct=take_profit_pct,
        )
        if not trade_decision.allowed:
            return CombinedRiskDecision(False, f"per-trade check failed: {trade_decision.reason}")

        portfolio_ok, portfolio_reason = self.portfolio.validate(
            balance, exposure, daily_loss_pct, open_positions, amount_usdt,
            side=side, reduce_only=reduce_only,
        )
        if not portfolio_ok:
            return CombinedRiskDecision(False, f"portfolio check failed: {portfolio_reason}")

        return CombinedRiskDecision(True, "Risk checks passed (server-observed portfolio + per-trade).",
                                    trade_decision.stop_loss_price, trade_decision.take_profit_price)

risk_engine = RiskEngine()
