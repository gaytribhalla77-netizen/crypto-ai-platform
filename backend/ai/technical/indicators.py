def sma(values, period):
    if len(values) < period:
        return None
    return sum(values[-period:]) / period

def pct_change(a, b):
    if not a:
        return 0.0
    return (b - a) / a * 100
