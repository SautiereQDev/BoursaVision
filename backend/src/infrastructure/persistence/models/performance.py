
"""
SQLAlchemy models for performance metrics (TimescaleDB).
"""
# ================================================================
# PLATEFORME TRADING - MODELES PERFORMANCE
# Modèles SQLAlchemy pour les métriques de performance (TimescaleDB)
# ================================================================

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, ForeignKey, Index, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from .base import Base, DatabaseMixin


class PortfolioPerformance(Base, DatabaseMixin):
    """Métriques de performance portfolio (snapshots quotidiens)"""

    __tablename__ = "portfolio_performance"

    time = Column(TIMESTAMP, primary_key=True, nullable=False)
    portfolio_id = Column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    # Valeurs
    total_value = Column(Numeric(15, 4), nullable=False)
    cash_value = Column(Numeric(15, 4), nullable=False)
    invested_value = Column(Numeric(15, 4), nullable=False)

    # Returns
    daily_return = Column(Numeric(8, 4))
    weekly_return = Column(Numeric(8, 4))
    monthly_return = Column(Numeric(8, 4))
    yearly_return = Column(Numeric(8, 4))
    inception_return = Column(Numeric(8, 4))

    # Métriques de risque
    volatility_30d = Column(Numeric(8, 4))
    sharpe_ratio_30d = Column(Numeric(8, 4))
    max_drawdown_30d = Column(Numeric(8, 4))
    beta_30d = Column(Numeric(8, 4))
    alpha_30d = Column(Numeric(8, 4))

    # Diversification
    number_of_positions = Column(Integer)
    largest_position_pct = Column(Numeric(5, 2))
    sector_concentration = Column(Numeric(5, 2))

    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    # Relations
    portfolio = relationship("Portfolio", back_populates="performance_snapshots")

    __table_args__ = (
        Index("idx_portfolio_performance_portfolio_time", "portfolio_id", "time"),
        # TimescaleDB hypertable sera créé via migration
    )


class Performance(Base):
    """
    Represents the performance metrics stored in the database.

    Attributes:
        id (UUID): The unique identifier for the performance record. Automatically
            generated as a UUID.
        metric (str): The name of the performance metric (e.g., accuracy, precision).
            Limited to 100 characters and cannot be null.
        value (Decimal): The value of the performance metric, stored as a numeric
            value with up to 15 digits and 4 decimal places. Cannot be null.
    """

    __tablename__ = "performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    metric = Column(String(100), nullable=False)
    value = Column(Numeric(15, 4), nullable=False)
