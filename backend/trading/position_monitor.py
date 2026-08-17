class PositionMonitor:
    def evaluate(self, side, entry, current, stop, take, highest=None):
        side = side.upper()
        pnl = ((current-entry)/entry*100) if side=="BUY" else ((entry-current)/entry*100)
        return {
            "pnl_percent": round(pnl,4),
            "stop_loss": current <= stop if side=="BUY" else current >= stop,
            "take_profit": current >= take if side=="BUY" else current <= take,
            "action": "EXIT" if ((current <= stop if side=="BUY" else current >= stop) or
                                 (current >= take if side=="BUY" else current <= take)) else "HOLD"
        }
