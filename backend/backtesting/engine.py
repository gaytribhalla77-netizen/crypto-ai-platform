from dataclasses import dataclass

@dataclass
class BacktestResult:
    trades:int; wins:int; losses:int; return_pct:float; max_drawdown_pct:float; profit_factor:float
    fees_paid:float=0.0; slippage_paid:float=0.0; win_rate_pct:float=0.0


def run_backtest(closes, initial=1000.0, fee_rate=0.001, slippage_rate=0.0005,
                 signal_fn=None, stop_loss_pct=0.02, take_profit_pct=0.04):
    """Long/flat event backtester. signal_fn(index, closes)->BUY/SELL/None.
    Includes fees and symmetric slippage; default strategy is buy-hold for backwards compatibility."""
    if len(closes)<2:return BacktestResult(0,0,0,0,0,0)
    equity=float(initial); peak=equity; max_dd=0.0; wins=losses=0; gp=gl=fees=slip=0.0
    in_pos=False; entry=0.0
    for i in range(len(closes)):
        p=float(closes[i])
        sig=(signal_fn(i, closes) if signal_fn else ("BUY" if i==0 else None))
        if not in_pos and sig=="BUY":
            cost=equity*fee_rate; sl=equity*slippage_rate; equity-=cost+sl; fees+=cost; slip+=sl; entry=p*(1+slippage_rate); in_pos=True
        if in_pos:
            ret=(p-entry)/entry
            if sig=="SELL" or ret<=-stop_loss_pct or ret>=take_profit_pct or i==len(closes)-1:
                gross=equity*ret; fee=abs(equity+gross)*fee_rate; sl=abs(equity+gross)*slippage_rate
                pnl=gross-fee-sl; equity+=pnl; fees+=fee; slip+=sl
                if pnl>0:wins+=1;gp+=pnl
                elif pnl<0:losses+=1;gl+=abs(pnl)
                in_pos=False
        peak=max(peak,equity); max_dd=max(max_dd,(peak-equity)/peak*100 if peak else 0)
    pf=gp/gl if gl else (float("inf") if gp else 0.0)
    return BacktestResult(wins+losses,wins,losses,(equity/initial-1)*100,max_dd,pf,fees,slip,100*wins/max(wins+losses,1))
