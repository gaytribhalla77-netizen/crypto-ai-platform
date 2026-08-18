from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from time import perf_counter

from backtesting.engine import run_backtest


@dataclass(frozen=True)
class Step6Gate:
    name: str
    passed: bool
    detail: str


def _series(n: int = 10_000) -> list[float]:
    """Deterministic 10k-bar stress fixture with alternating trend regimes."""
    out: list[float] = []
    price = 100.0
    for i in range(n):
        drift = 0.0008 if (i // 500) % 2 == 0 else -0.0006
        shock = ((i * 37) % 101 - 50) / 1_000_000
        price *= 1.0 + drift + shock
        out.append(price)
    return out


def run_offline_step6_gates() -> list[Step6Gate]:
    closes = _series()
    started = perf_counter()
    result = run_backtest(closes, initial=1000.0)
    elapsed = perf_counter() - started

    metrics = (
        result.return_pct,
        result.max_drawdown_pct,
        result.fees_paid,
        result.slippage_paid,
    )
    return [
        Step6Gate("deterministic_backtest", result.trades > 0, f"trades={result.trades}"),
        Step6Gate("finite_metrics", all(isfinite(float(x)) for x in metrics), "metrics finite"),
        Step6Gate("drawdown_bounded", 0 <= result.max_drawdown_pct <= 100, f"max_drawdown_pct={result.max_drawdown_pct:.4f}"),
        Step6Gate("cost_accounting", result.fees_paid >= 0 and result.slippage_paid >= 0, f"fees={result.fees_paid:.6f}, slippage={result.slippage_paid:.6f}"),
        Step6Gate("performance", elapsed < 2.0, f"10k bars in {elapsed:.4f}s"),
    ]


def offline_step6_passes() -> bool:
    return all(g.passed for g in run_offline_step6_gates())
