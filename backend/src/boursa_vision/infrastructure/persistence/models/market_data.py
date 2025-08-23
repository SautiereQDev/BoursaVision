"""
SQLAlchemy models for market data, indicators, and signals (TimescaleDB).
"""
# ================================================================
# PLATEFORME TRADING - MODELES DONNEES DE MARCHE
# Modèles SQLAlchemy pour TimescaleDB (market data, indicateurs, signaux)
# ================================================================

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Index,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

from .base import Base, DatabaseMixin


class MarketData(Base, DatabaseMixin):
    """Données de marché OHLCV (TimescaleDB Hypertable)"""

    __tablename__ = "market_data"

    time = Column(TIMESTAMP, primary_key=True, nullable=False)
    symbol = Column(String(20), primary_key=True, nullable=False)
    interval_type = Column(String(5), primary_key=True, nullable=False)
    open_price = Column(Numeric(15, 4))
    high_price = Column(Numeric(15, 4))
    low_price = Column(Numeric(15, 4))
    close_price = Column(Numeric(15, 4))
    adjusted_close = Column(Numeric(15, 4))
    volume = Column(BigInteger)
    source = Column(String(20), default="yfinance")
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_market_data_symbol_time", "symbol", "time"),
        Index("idx_market_data_interval", "interval_type", "time"),
        {"extend_existing": True},
    )


# Clear the registry to avoid duplicate registration


class TechnicalIndicator(Base, DatabaseMixin):
    """Indicateurs techniques calculés (TimescaleDB Hypertable)"""

    __tablename__ = "technical_indicators"

    time = Column(TIMESTAMP, primary_key=True, nullable=False)
    symbol = Column(String(20), primary_key=True, nullable=False)
    indicator_name = Column(String(30), primary_key=True, nullable=False)
    timeframe = Column(String(5), primary_key=True, nullable=False)
    value = Column(Numeric(15, 6))
    value_secondary = Column(Numeric(15, 6))
    value_tertiary = Column(Numeric(15, 6))
    parameters = Column(JSONB)  # Paramètres de calcul ex: {"period": 14}
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(UTC))

    __table_args__ = {"extend_existing": True}  # noqa: RUF012


# Clear the registry to avoid duplicate registration


class Signal(Base, DatabaseMixin):
    """Signaux d'investissement générés (TimescaleDB Hypertable)"""

    __tablename__ = "signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    time = Column(TIMESTAMP, nullable=False, index=True)
    symbol = Column(String(20), nullable=False)
    signal_type = Column(String(10), nullable=False)
    strength = Column(String(10), nullable=False)
    confidence_score = Column(Numeric(3, 2), nullable=False)
    price_target = Column(Numeric(15, 4))
    stop_loss = Column(Numeric(15, 4))
    rationale = Column(Text)
    technical_score = Column(Numeric(3, 2))
    fundamental_score = Column(Numeric(3, 2))
    market_context_score = Column(Numeric(3, 2))
    indicators_used = Column(JSONB)
    signal_metadata = Column(JSONB)
    is_active = Column(Boolean, default=True)
    expires_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(UTC))

    __table_args__ = (
        CheckConstraint(
            "signal_type IN ('BUY', 'SELL', 'HOLD')", name="check_signal_type"
        ),
        CheckConstraint(
            "strength IN ('WEAK', 'MODERATE', 'STRONG')", name="check_strength"
        ),
        CheckConstraint(
            "confidence_score BETWEEN 0.00 AND 1.00",
            name="check_confidence_score",
        ),
        Index("idx_signals_symbol_time", "symbol", "time"),
        Index("idx_signals_active", "is_active", "time"),
        Index("idx_signals_type", "signal_type", "time"),
        {"extend_existing": True},
    )
