from decimal import Decimal

def floor_to_step(quantity, step):
    q, s = Decimal(str(quantity)), Decimal(str(step))
    return float((q // s) * s)

def validate_order_filters(quantity, price, min_qty, max_qty, step_size, min_notional):
    q, p = Decimal(str(quantity)), Decimal(str(price))
    if q < Decimal(str(min_qty)): return False, "Quantity below minimum."
    if q > Decimal(str(max_qty)): return False, "Quantity above maximum."
    if q * p < Decimal(str(min_notional)): return False, "Minimum notional not met."
    if floor_to_step(q, step_size) != float(q): return False, "Quantity precision invalid."
    return True, "OK"
