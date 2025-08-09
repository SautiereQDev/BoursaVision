# ================================================================
# PLATEFORME TRADING - MODELES INSTRUMENTS
# Modèles SQLAlchemy pour les instruments financiers
# ================================================================

import uuid

from sqlalchemy import Boolean, CheckConstraint, Column, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, DatabaseMixin
from .mixins import TimestampMixin


class Instrument(Base, DatabaseMixin, TimestampMixin):
    """Instruments financiers"""

    __tablename__ = "instruments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, unique=True, index=True)
    name = Column(String(200))
    instrument_type = Column(String(20), nullable=False)
    exchange = Column(String(10))
    currency = Column(String(3))
    sector = Column(String(50))
    industry = Column(String(100))
    country = Column(String(2))
    isin = Column(String(12))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    # created_at, updated_at fournis par TimestampMixin

    # Relations
    positions = relationship("Position", back_populates="instrument")
    transactions = relationship("Transaction", back_populates="instrument")
    fundamental_data = relationship("FundamentalData", back_populates="instrument")

    __table_args__ = (
        CheckConstraint(
            "instrument_type IN ("
            "'stock', 'etf', 'bond', 'crypto', 'forex', 'commodity')",
            name="check_instrument_type",
        ),
        Index("idx_instruments_symbol", "symbol"),
        Index("idx_instruments_type", "instrument_type"),
        Index("idx_instruments_active", "is_active"),
    )
