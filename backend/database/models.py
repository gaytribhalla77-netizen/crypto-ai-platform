from sqlalchemy import String, Float, Boolean, DateTime, Text, Integer, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)

class Trade(Base):
    __tablename__ = "trades"
    __table_args__ = (UniqueConstraint("user_id", "client_request_id", name="uq_trade_user_client_request"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    amount_usdt: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(32), default="PENDING")
    exchange_order_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    client_request_id: Mapped[str] = mapped_column(String(80), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    side: Mapped[str] = mapped_column(String(8))
    quantity: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    stop_loss_price: Mapped[float] = mapped_column(Float)
    take_profit_price: Mapped[float] = mapped_column(Float)
    protection_order_list_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="OPEN")

class AuditEvent(Base):
    __tablename__ = "audit_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    event_type: Mapped[str] = mapped_column(String(64))
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Prediction(Base):
    __tablename__ = "predictions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(32), index=True)
    interval: Mapped[str] = mapped_column(String(8))
    horizon_candles: Mapped[int] = mapped_column(Integer)
    direction: Mapped[str] = mapped_column(String(8))
    confidence: Mapped[float] = mapped_column(Float)
    probability_up: Mapped[float] = mapped_column(Float)
    entry_price: Mapped[float] = mapped_column(Float)
    model_version: Mapped[str] = mapped_column(String(64))
    target_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    exit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class DailyEquitySnapshot(Base):
    """Server-owned start-of-day equity baseline used for daily-loss gating.

    One row per user/day. The first authenticated trading request of a day
    establishes the baseline from the configured exchange account; subsequent
    risk checks compare current server-observed equity against that baseline.
    """
    __tablename__ = "daily_equity_snapshots"
    __table_args__ = (UniqueConstraint("user_id", "date_key", name="uq_daily_equity_user_date"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    date_key: Mapped[str] = mapped_column(String(10), index=True)
    starting_equity_usdt: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class SecuritySetting(Base):
    __tablename__ = "security_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    totp_secret_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    kill_switch: Mapped[bool] = mapped_column(Boolean, default=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class CredentialVault(Base):
    __tablename__ = "credential_vault"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    provider: Mapped[str] = mapped_column(String(64))
    encrypted_payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrderReconciliation(Base):
    __tablename__ = "order_reconciliations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trade_id: Mapped[int] = mapped_column(Integer, index=True)
    exchange_status: Mapped[str] = mapped_column(String(32))
    executed_qty: Mapped[float] = mapped_column(Float, default=0.0)
    avg_price: Mapped[float] = mapped_column(Float, default=0.0)
    raw_payload: Mapped[str] = mapped_column(Text)
    reconciled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
