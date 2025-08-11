"""
SQLAlchemy models for company fundamental data.
"""
# ================================================================
# PLATEFORME TRADING - MODELES DONNEES FONDAMENTALES
# Modèles SQLAlchemy pour les données fondamentales des entreprises
# ================================================================

import uuid

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, DatabaseMixin
from .mixins import TimestampMixin


class FundamentalData(Base, DatabaseMixin, TimestampMixin):
    """Données fondamentales des entreprises"""

    __tablename__ = "fundamental_data"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id = Column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False
    )
    symbol = Column(String(20), nullable=False)
    period_end_date = Column(Date, nullable=False)
    period_type = Column(String(10), nullable=False)

    # Données de base
    market_cap = Column(BigInteger)
    enterprise_value = Column(BigInteger)
    shares_outstanding = Column(BigInteger)
    float_shares = Column(BigInteger)

    # Ratios de valorisation
    pe_ratio = Column(Numeric(8, 2))
    forward_pe = Column(Numeric(8, 2))
    peg_ratio = Column(Numeric(8, 2))
    price_to_book = Column(Numeric(8, 2))
    price_to_sales = Column(Numeric(8, 2))
    enterprise_value_revenue = Column(Numeric(8, 2))
    enterprise_value_ebitda = Column(Numeric(8, 2))

    # Profitabilité
    profit_margin = Column(Numeric(8, 4))
    operating_margin = Column(Numeric(8, 4))
    return_on_assets = Column(Numeric(8, 4))
    return_on_equity = Column(Numeric(8, 4))
    return_on_investment = Column(Numeric(8, 4))

    # Croissance
    revenue_growth = Column(Numeric(8, 4))
    earnings_growth = Column(Numeric(8, 4))
    earnings_growth_quarterly = Column(Numeric(8, 4))

    # Structure financière
    debt_to_equity = Column(Numeric(8, 4))
    current_ratio = Column(Numeric(8, 4))
    quick_ratio = Column(Numeric(8, 4))

    # Dividendes
    dividend_yield = Column(Numeric(8, 4))
    payout_ratio = Column(Numeric(8, 4))
    dividend_growth_5y = Column(Numeric(8, 4))

    # Autres
    beta = Column(Numeric(8, 4))

    # created_at, updated_at fournis par TimestampMixin

    # Relations
    instrument = relationship("Instrument", back_populates="fundamental_data")

    __table_args__ = (
        UniqueConstraint(
            "symbol",
            "period_end_date",
            "period_type",
            name="uq_fundamental_period",
        ),
        CheckConstraint(
            "period_type IN ('QUARTERLY', 'ANNUAL')", name="check_period_type"
        ),
        Index("idx_fundamental_data_symbol", "symbol", "period_end_date"),
    )
