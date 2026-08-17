import re

# Reuse the same coin keyword map the news engine uses, so "bitcoin" /
# "btc" resolve to the same symbol everywhere in the app.
from news.engine import ASSET_KEYWORDS

_SYMBOL_LOOKUP = {}
for symbol, keywords in ASSET_KEYWORDS.items():
    for kw in keywords:
        _SYMBOL_LOOKUP[kw] = symbol

BUY_WORDS = ["khareed", "kharido", "kharidna", "buy", "purchase"]
SELL_WORDS = ["bech", "becho", "bechna", "sell"]
PRICE_WORDS = ["price", "kimat", "keemat", "bhav", "rate", "kitna hai", "kitne ka"]
PORTFOLIO_WORDS = ["portfolio", "profit loss", "profit-loss", "mera paisa", "invest"]
WATCHLIST_WORDS = ["watchlist", "coins dikhao", "sab coin", "market dikhao"]
POSITIONS_WORDS = ["open position", "positions", "position dikhao"]
HISTORY_WORDS = ["history", "order history", "trade history", "journal"]
NEWS_WORDS = ["news", "khabar", "khabren"]
INFO_WORDS = ["jankari", "poori jankari", "sab batao", "detail", "details", "analysis",
              "info", "information", "bare me batao", "ke bare me"]
CONFIRM_WORDS = ["haan", "han", "yes", "confirm", "theek hai", "kar do", "ok", "okay"]
CANCEL_WORDS = ["nahi", "no", "cancel", "mat karo", "ruk jao", "rehne do"]

_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)")


def _find_symbol(text: str) -> str | None:
    for kw, symbol in sorted(_SYMBOL_LOOKUP.items(), key=lambda x: -len(x[0])):
        if kw in text:
            return symbol
    return None


def _find_amount(text: str) -> float | None:
    m = _NUMBER_RE.search(text)
    return float(m.group(1)) if m else None


def _contains_any(text: str, words: list[str]) -> bool:
    return any(w in text for w in words)


class VoiceService:
    """Stateless NLU: text in, structured intent out. Never touches the
    database or an exchange. Trade intents are always returned with
    requires_confirmation=True and no side effects -- the caller (frontend)
    is responsible for showing the confirmation and then calling the
    normal, already risk-gated order endpoint (/api/v06/testnet/order)
    itself. This module does not, and must not, place orders."""

    def normalize(self, text: str) -> str:
        return " ".join(text.strip().lower().split())

    async def handle(self, text: str) -> dict:
        norm = self.normalize(text)

        if _contains_any(norm, CONFIRM_WORDS) and len(norm.split()) <= 3:
            return {"intent": "confirm", "input": norm}
        if _contains_any(norm, CANCEL_WORDS) and len(norm.split()) <= 3:
            return {"intent": "cancel", "input": norm}

        is_buy = _contains_any(norm, BUY_WORDS)
        is_sell = _contains_any(norm, SELL_WORDS)
        if is_buy or is_sell:
            symbol = _find_symbol(norm)
            amount = _find_amount(norm)
            missing = []
            if not symbol:
                missing.append("symbol")
            if not amount:
                missing.append("amount")
            return {
                "intent": "trade",
                "input": norm,
                "side": "BUY" if is_buy else "SELL",
                "symbol": symbol,
                "amount_usdt": amount,
                "missing": missing,
                "requires_confirmation": True,
                "message": (
                    f"{'Kharidna' if is_buy else 'Bechna'} hai {amount or '?'} dollar ka "
                    f"{symbol.replace('USDT', '') if symbol else '?'}. Confirm karein?"
                    if missing == [] else
                    f"Mujhe symbol aur amount dono chahiye — sirf yeh mila: symbol={symbol}, amount={amount}."
                ),
            }

        if _contains_any(norm, INFO_WORDS):
            symbol = _find_symbol(norm)
            return {"intent": "info", "input": norm, "symbol": symbol,
                     "missing": [] if symbol else ["symbol"]}

        if _contains_any(norm, PRICE_WORDS):
            symbol = _find_symbol(norm)
            return {"intent": "price", "input": norm, "symbol": symbol,
                     "missing": [] if symbol else ["symbol"]}

        if _contains_any(norm, PORTFOLIO_WORDS):
            return {"intent": "portfolio", "input": norm}

        if _contains_any(norm, POSITIONS_WORDS):
            return {"intent": "positions", "input": norm}

        if _contains_any(norm, HISTORY_WORDS):
            return {"intent": "history", "input": norm}

        if _contains_any(norm, WATCHLIST_WORDS):
            return {"intent": "watchlist", "input": norm}

        if _contains_any(norm, NEWS_WORDS):
            symbol = _find_symbol(norm)
            return {"intent": "news", "input": norm, "symbol": symbol,
                     "missing": [] if symbol else ["symbol"]}

        return {
            "intent": "unknown", "input": norm,
            "message": "Samajh nahi aaya. Price, portfolio, watchlist, history, ya buy/sell bol ke try karein.",
        }
