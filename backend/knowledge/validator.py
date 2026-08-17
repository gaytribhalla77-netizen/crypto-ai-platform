from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class ValidationReport:
    strategy: str
    status: str
    reasons: list[str]
    metrics: dict

class StrategyValidator:
    """Promotion gate: rejects incomplete or non-robust backtests."""
    REQUIRED=("sample_size","return_pct","max_drawdown_pct","win_rate","profit_factor","fees_modelled","slippage_modelled","lookahead_checked")
    def validate(self, strategy_name: str, metrics: dict[str,Any]) -> dict:
        missing=[k for k in self.REQUIRED if k not in metrics]
        reasons=[]
        if missing: reasons.append("missing:"+",".join(missing))
        if metrics.get("lookahead_checked") is False: reasons.append("lookahead_bias_not_cleared")
        if metrics.get("fees_modelled") is False: reasons.append("fees_not_modelled")
        if metrics.get("slippage_modelled") is False: reasons.append("slippage_not_modelled")
        if float(metrics.get("max_drawdown_pct",0) or 0) >= 30: reasons.append("drawdown_too_high")
        status="VALIDATED" if not reasons else "QUARANTINED"
        return asdict(ValidationReport(strategy_name,status,reasons,metrics))
