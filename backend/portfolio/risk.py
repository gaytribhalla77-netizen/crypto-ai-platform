class PortfolioRisk:
    def __init__(self, max_exposure_pct=25.0, max_daily_loss_pct=5.0, max_positions=5):
        self.max_exposure_pct = max_exposure_pct
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_positions = max_positions

    def validate(self, balance, exposure, daily_loss_pct, open_positions, amount, *, side="BUY", reduce_only=False):
        if balance <= 0:
            return False, "No available USDT balance."
        if daily_loss_pct >= self.max_daily_loss_pct and not reduce_only:
            return False, "Daily loss limit reached; only protective exits are allowed."
        if side == "BUY" and not reduce_only:
            if open_positions >= self.max_positions:
                return False, "Maximum open positions reached."
            projected_exposure = exposure + amount
            if projected_exposure / max(balance + exposure, 1e-9) * 100 > self.max_exposure_pct:
                return False, "Portfolio exposure limit reached."
        return True, "OK"
