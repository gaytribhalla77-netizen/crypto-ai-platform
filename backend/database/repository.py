from sqlalchemy import select, update, desc
import json
from sqlalchemy.exc import IntegrityError
from database.models import Trade, Position, AuditEvent, Prediction


class DuplicateTradeRequest(Exception):
    """Raised when a client_request_id has already been used — the caller
    must treat this as 'do not resubmit to the exchange', not as a generic
    error to retry."""
    def __init__(self, existing_trade: Trade):
        self.existing_trade = existing_trade
        super().__init__(f"Duplicate client_request_id: trade {existing_trade.id} already exists.")


class TradeRepository:
    def __init__(self, session):
        self.session = session

    async def get_by_client_request_id(self, client_request_id: str, user_id: int) -> Trade | None:
        result = await self.session.execute(
            select(Trade).where(Trade.user_id == user_id, Trade.client_request_id == client_request_id)
        )
        return result.scalar_one_or_none()

    async def create_idempotent(self, **kwargs) -> Trade:
        """Create a trade row, enforcing the unique client_request_id at the
        database level (not just an in-process check, which would race under
        concurrent requests). Raises DuplicateTradeRequest instead of
        silently creating a second trade."""
        existing = await self.get_by_client_request_id(kwargs["client_request_id"], kwargs["user_id"])
        if existing is not None:
            raise DuplicateTradeRequest(existing)
        obj = Trade(**kwargs)
        self.session.add(obj)
        try:
            await self.session.commit()
        except IntegrityError:
            # Lost a race with a concurrent identical request between the
            # check above and this commit — the unique DB constraint is the
            # real backstop. Roll back and surface the existing row.
            await self.session.rollback()
            existing = await self.get_by_client_request_id(kwargs["client_request_id"], kwargs["user_id"])
            raise DuplicateTradeRequest(existing) from None
        await self.session.refresh(obj)
        return obj

    async def create(self, **kwargs):
        # Back-compat shim. Prefer create_idempotent for anything that will
        # reach the exchange.
        return await self.create_idempotent(**kwargs)

    async def update_status(self, trade_id, status, order_id=None):
        values = {"status": status}
        if order_id is not None:
            values["exchange_order_id"] = str(order_id)
        await self.session.execute(update(Trade).where(Trade.id == trade_id).values(**values))
        await self.session.commit()

    async def list_by_user(self, user_id: int, limit: int = 100) -> list[Trade]:
        # Order history / journal: newest first. This is read-only and just
        # surfaces what's already persisted on every order attempt.
        result = await self.session.execute(
            select(Trade).where(Trade.user_id == user_id)
            .order_by(desc(Trade.created_at)).limit(limit)
        )
        return list(result.scalars().all())


class PositionRepository:
    def __init__(self, session):
        self.session = session

    async def open_positions(self, user_id):
        result = await self.session.execute(
            select(Position).where(Position.user_id == user_id, Position.status == "OPEN")
        )
        return list(result.scalars().all())

    async def all_open_positions(self):
        # Used by the background position-monitor worker, which has to scan
        # across every user, not just one.
        result = await self.session.execute(select(Position).where(Position.status == "OPEN"))
        return list(result.scalars().all())

    async def open_position_for_symbol(self, user_id: int, symbol: str) -> Position | None:
        result = await self.session.execute(
            select(Position).where(
                Position.user_id == user_id,
                Position.symbol == symbol.upper(),
                Position.status == "OPEN",
            ).order_by(Position.id)
        )
        return result.scalars().first()

    async def create(self, **kwargs) -> Position:
        obj = Position(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def close(self, position_id: int) -> None:
        await self.session.execute(
            update(Position).where(Position.id == position_id).values(status="CLOSED")
        )
        await self.session.commit()


class AuditRepository:
    def __init__(self, session):
        self.session = session

    async def record(self, event_type, payload, user_id=None):
        obj = AuditEvent(user_id=user_id, event_type=event_type, payload=json.dumps(payload, default=str, separators=(",", ":")))
        self.session.add(obj)
        await self.session.commit()
        return obj


class PredictionRepository:
    """Stores every model prediction and its eventual outcome. This is what
    makes the AI's confidence numbers checkable instead of just asserted —
    see resolve_due() and accuracy_stats()."""
    def __init__(self, session):
        self.session = session

    async def create(self, **kwargs) -> Prediction:
        obj = Prediction(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def due_unresolved(self, now):
        result = await self.session.execute(
            select(Prediction).where(Prediction.resolved.is_(False), Prediction.target_time <= now)
        )
        return list(result.scalars().all())

    async def resolve(self, prediction_id: int, exit_price: float, correct: bool):
        await self.session.execute(
            update(Prediction).where(Prediction.id == prediction_id)
            .values(resolved=True, exit_price=exit_price, correct=correct)
        )
        await self.session.commit()

    async def accuracy_stats(self, symbol: str | None = None, limit: int = 200):
        query = select(Prediction).where(Prediction.resolved.is_(True))
        if symbol:
            query = query.where(Prediction.symbol == symbol.upper())
        query = query.order_by(desc(Prediction.created_at)).limit(limit)
        result = await self.session.execute(query)
        rows = list(result.scalars().all())
        total = len(rows)
        correct = sum(1 for r in rows if r.correct)
        return {
            "sample_size": total,
            "correct": correct,
            "accuracy_pct": round(correct / total * 100, 1) if total else None,
            "note": "Based on the last resolved predictions actually made by this model — "
                    "not a claim about future performance.",
        }

    async def recent(self, symbol: str | None = None, limit: int = 20):
        query = select(Prediction)
        if symbol:
            query = query.where(Prediction.symbol == symbol.upper())
        query = query.order_by(desc(Prediction.created_at)).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())
