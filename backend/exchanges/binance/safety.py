from decimal import Decimal, ROUND_DOWN, ROUND_UP


def symbol_filters(exchange_info: dict, symbol: str):
    row = next((x for x in exchange_info.get("symbols", []) if x.get("symbol", "").upper() == symbol.upper()), None)
    if not row:
        raise RuntimeError(f"Symbol {symbol.upper()} is not available on Binance.")
    out = {}
    for f in row.get("filters", []):
        t = f.get("filterType")
        if t == "LOT_SIZE": out["min_qty"], out["max_qty"], out["step"] = float(f["minQty"]), float(f["maxQty"]), float(f["stepSize"])
        elif t == "MARKET_LOT_SIZE": out["market_min_qty"], out["market_max_qty"], out["market_step"] = float(f["minQty"]), float(f["maxQty"]), float(f["stepSize"])
        elif t == "PRICE_FILTER": out["tick"] = float(f["tickSize"])
        elif t in ("MIN_NOTIONAL", "NOTIONAL"): out["min_notional"] = float(f.get("minNotional", f.get("notional", 0)))
    for k in ("min_qty", "max_qty", "step", "tick", "min_notional"):
        if k not in out: raise RuntimeError(f"Missing Binance filter {k} for {symbol.upper()}.")
    return out


def floor_step(value: float, step: float) -> float:
    if step <= 0: return value
    d, s = Decimal(str(value)), Decimal(str(step))
    return float((d // s) * s)


def price_tick(value: float, tick: float, *, up: bool = False) -> float:
    d, t = Decimal(str(value)), Decimal(str(tick))
    units = (d / t).to_integral_value(rounding=ROUND_UP if up else ROUND_DOWN)
    return float(units * t)
