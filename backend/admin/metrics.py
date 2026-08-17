class AdminMetrics:
    def aggregate(self, trades):
        total = len(trades)
        wins = sum(1 for t in trades if getattr(t,"pnl",0) > 0)
        return {"trades":total,"wins":wins,"losses":total-wins,
                "win_rate_pct": round(wins/total*100,2) if total else 0}
