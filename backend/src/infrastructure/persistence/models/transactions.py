"""
SQLAlchemy models for financial transactions.
"""
# ================================================================
# PLATEFORME TRADING - MODELES TRANSACTIONS
# Modèles SQLAlchemy pour les transactions financières
# ================================================================


from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import CheckConstraint, Column, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship

from .base import Base, DatabaseMixin
from .mixins import PortfolioInstrumentMixin


class Transaction(Base, DatabaseMixin, PortfolioInstrumentMixin):
    """Transactions financières"""

    __tablename__ = "transactions"

    # id, portfolio_id, instrument_id, symbol fournis par PortfolioInstrumentMixin
    transaction_type = Column(String(10), nullable=False)
    quantity = Column(Numeric(15, 8), nullable=False)
    price = Column(Numeric(15, 4), nullable=False)
    amount = Column(Numeric(15, 4), nullable=False)  # quantity * price
    fees = Column(Numeric(15, 4), default=Decimal("0.0000"))
    taxes = Column(Numeric(15, 4), default=Decimal("0.0000"))
    net_amount = Column(Numeric(15, 4), nullable=False)
    currency = Column(String(3), nullable=False)
    exchange_rate = Column(Numeric(10, 6), default=Decimal("1.000000"))
    notes = Column(Text)
    external_id = Column(String(100))  # ID transaction broker externe
    executed_at = Column(TIMESTAMP, nullable=False)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    # Relations
    portfolio = relationship("Portfolio", back_populates="transactions")
    instrument = relationship("Instrument", back_populates="transactions")

    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('BUY', 'SELL', 'DIVIDEND', 'SPLIT', 'SPIN_OFF')",
            name="check_transaction_type",
        ),
        Index("idx_transactions_portfolio", "portfolio_id"),
        Index("idx_transactions_symbol", "symbol"),
        Index("idx_transactions_date", "executed_at"),
        Index("idx_transactions_type", "transaction_type"),
    )
