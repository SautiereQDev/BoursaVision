"""
Investment SQLAlchemy model.
"""

from sqlalchemy import Column, DateTime, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from .base import Base


class InvestmentModel(Base):
    """SQLAlchemy model for investments."""

    __tablename__ = "investments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    exchange = Column(String(50), nullable=False, index=True)
    sector = Column(String(100), nullable=True, index=True)
    industry = Column(String(100), nullable=True)
    market_cap = Column(Numeric(20, 2), nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now()  # pylint: disable=not-callable
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),  # pylint: disable=not-callable
        onupdate=func.now(),  # pylint: disable=not-callable
    )
