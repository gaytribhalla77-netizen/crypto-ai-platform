from dataclasses import dataclass

@dataclass
class RiskDecision:
    allowed: bool
    reason: str
    stop_loss_price: float | None = None
    take_profit_price: float | None = None

class ProductionRiskManager:
    """Fail-closed baseline risk manager.

    This module calculates protection levels but does not place live orders.
    """
    def __init__(self, stop_loss_pct=5.0, take_profit_pct=5.0, max_auto_usdt=10.0):
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.max_auto_usdt = max_auto_usdt

    def validate(self, side, amount_usdt, entry_price, automatic=False,
                 stop_loss_pct=None, take_profit_pct=None):
        if amount_usdt <= 0:
            return RiskDecision(False, "Amount must be greater than zero.")
        if automatic and amount_usdt > self.max_auto_usdt:
            return RiskDecision(False, "Automatic opportunity limit exceeded.")
        if entry_price <= 0:
            return RiskDecision(False, "Invalid entry price.")

        # Let the caller (e.g. a user-facing "how much loss should I risk?"
        # prompt) override the instance defaults for this one order. Falls
        # back to the configured defaults when not supplied.
        sl_pct = self.stop_loss_pct if stop_loss_pct is None else float(stop_loss_pct)
        tp_pct = self.take_profit_pct if take_profit_pct is None else float(take_profit_pct)
        if sl_pct <= 0 or sl_pct > 100:
            return RiskDecision(False, "stop_loss_pct must be between 0 and 100.")
        if tp_pct <= 0 or tp_pct > 100:
            return RiskDecision(False, "take_profit_pct must be between 0 and 100.")

        if side.upper() == "BUY":
            sl = entry_price * (1 - sl_pct / 100)
            tp = entry_price * (1 + tp_pct / 100)
        else:
            sl = entry_price * (1 + sl_pct / 100)
            tp = entry_price * (1 - tp_pct / 100)

        if sl <= 0 or tp <= 0:
            return RiskDecision(False, "Protection levels must remain positive.")
        return RiskDecision(True, "Risk checks passed for paper/test execution.",
                            stop_loss_price=sl, take_profit_price=tp)
