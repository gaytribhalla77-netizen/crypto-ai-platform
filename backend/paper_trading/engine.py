from dataclasses import dataclass
import uuid

@dataclass
class PaperOrder:
    id: str
    symbol: str
    side: str
    amount_usdt: float
    status: str = "FILLED"

class PaperTradingEngine:
    def __init__(self, balance=1000.0):
        self.balance = balance
        self.orders = []

    def order(self, symbol, side, amount_usdt):
        if amount_usdt <= 0 or amount_usdt > self.balance:
            raise ValueError("Invalid paper-trading amount.")
        self.balance -= amount_usdt
        o = PaperOrder(uuid.uuid4().hex, symbol.upper(), side.upper(), amount_usdt)
        self.orders.append(o)
        return o
