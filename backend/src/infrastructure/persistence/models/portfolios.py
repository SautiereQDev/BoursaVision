# ================================================================
# PLATEFORME TRADING - MODELES PORTFOLIOS
# Modèles SQLAlchemy pour portfolios et positions
# ================================================================

import uuid
from collections import defaultdict
from decimal import Decimal
from typing import Dict, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from .base import Base, DatabaseMixin
from .mixins import PortfolioInstrumentMixin, TimestampMixin

CASCADE_ALL_DELETE_ORPHAN = "all, delete-orphan"


class Portfolio(Base, DatabaseMixin, TimestampMixin):
    """
    Portfolio Model

    Represents a user's investment portfolio, including details about cash,
    investments, performance, and relationships with other entities such as
    positions, transactions, and alerts.

    Attributes:
        id (UUID): Unique identifier for the portfolio.
        user_id (UUID): Foreign key referencing the user who owns the
        portfolio.
        name (str): Name of the portfolio (max length: 100 characters).
        description (str): Optional description of the portfolio.
        base_currency (str): Base currency of the portfolio (default: "USD").
        initial_cash (Decimal): Initial cash amount in the portfolio
        (default: 0.0000).
        current_cash (Decimal): Current cash amount in the portfolio
        (default: 0.0000).
        total_invested (Decimal): Total amount invested in the portfolio
        (default: 0.0000).
        total_value (Decimal): Total value of the portfolio (default: 0.0000).
        daily_pnl (Decimal): Daily profit and loss of the portfolio
        (default: 0.0000).
        total_pnl (Decimal): Total profit and loss of the portfolio
        (default: 0.0000).
        daily_return_pct (Decimal): Daily return percentage of the portfolio
        (default: 0.0000).
        total_return_pct (Decimal): Total return percentage of the portfolio
        (default: 0.0000).
        is_default (bool): Indicates if this is the default portfolio
        for the user
        (default: False).
        is_active (bool): Indicates if the portfolio is active (default: True).

    Relationships:
        positions (list): List of positions associated with the portfolio.
        transactions (list): List of transactions associated with the
        portfolio.
        performance_snapshots (list): List of performance snapshots for the
        portfolio.
        alerts (list): List of alerts associated with the portfolio.
        user (User): The user who owns the portfolio.

    Table Constraints:
        - CheckConstraint: Ensures `base_currency` is one of 'USD', 'EUR',
        'GBP', 'CAD', 'JPY'.
        - Index: Index on `user_id` for efficient querying.
        - Index: Composite index on `user_id` and `is_default`.

    Methods:
        calculate_total_value(
            current_prices: Optional[Dict] = None
        ) -> Decimal:
            Calculates the total value of the portfolio, including cash and
            active positions.
            Args:
                current_prices (Optional[Dict]): A dictionary of current
                prices for symbols.
            Returns:
                Decimal: The total value of the portfolio.

        get_active_positions() -> List[Position]:
            Returns a list of active positions in the portfolio.

        get_largest_position() -> Optional[Position]:
            Returns the largest position by percentage in the portfolio.
            Returns:
                Position: The position with the highest weight percentage, or
                None if no active positions exist.

        get_sector_allocation() -> Dict[str, float]:
            Returns the allocation of the portfolio by sector.
            Returns:
                Dict[str, float]: A dictionary mapping sectors to their
                allocation percentages.
    """

    __tablename__ = "portfolios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
    )
    name = Column(String(100), nullable=False)
    description = Column(Text)
    base_currency = Column(String(3), default="USD")
    initial_cash = Column(Numeric(15, 4), default=Decimal("0.0000"))
    current_cash = Column(Numeric(15, 4), default=Decimal("0.0000"))
    total_invested = Column(Numeric(15, 4), default=Decimal("0.0000"))
    total_value = Column(Numeric(15, 4), default=Decimal("0.0000"))
    daily_pnl = Column(Numeric(15, 4), default=Decimal("0.0000"))
    total_pnl = Column(Numeric(15, 4), default=Decimal("0.0000"))
    daily_return_pct = Column(Numeric(8, 4), default=Decimal("0.0000"))
    total_return_pct = Column(Numeric(8, 4), default=Decimal("0.0000"))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    # created_at, updated_at fournis par TimestampMixin
    # Relations
    positions = relationship(
        "Position",
        back_populates="portfolio",
        cascade=CASCADE_ALL_DELETE_ORPHAN,
    )
    transactions = relationship(
        "Transaction",
        back_populates="portfolio",
        cascade=CASCADE_ALL_DELETE_ORPHAN,
    )
    performance_snapshots = relationship(
        "PortfolioPerformance",
        back_populates="portfolio",
        cascade=CASCADE_ALL_DELETE_ORPHAN,
    )
    alerts = relationship("Alert", back_populates="portfolio")
    user = relationship("User", back_populates="portfolios")

    __table_args__ = (
        CheckConstraint(
            "base_currency IN ('USD', 'EUR', 'GBP', 'CAD', 'JPY')",
            name="check_base_currency",
        ),
        Index("idx_portfolios_user", "user_id"),
        Index("idx_portfolios_default", "user_id", "is_default"),
    )

    def calculate_total_value(self, current_prices: Optional[Dict] = None):
        """Calculates the total value of the portfolio"""
        total = self.current_cash
        if current_prices:
            for position in self.positions:
                if position.is_active and position.symbol in current_prices:
                    market_price = current_prices[position.symbol]
                    total += position.quantity * market_price
        return total

    def get_active_positions(self):
        """Returns active positions"""
        return [p for p in self.positions if p.is_active]

    def get_largest_position(self):
        """Returns the largest position by percentage"""
        active_positions = self.get_active_positions()
        if not active_positions:
            return None
        return max(active_positions, key=lambda p: p.weight_pct)

    def get_sector_allocation(self):
        """Returns allocation by sector"""

        sector_allocation = defaultdict(float)

        for position in self.get_active_positions():
            if position.instrument and position.instrument.sector:
                sector_allocation[position.instrument.sector] += float(
                    position.weight_pct
                )

        return dict(sector_allocation)


class Position(Base, DatabaseMixin, PortfolioInstrumentMixin, TimestampMixin):
    """Current positions in portfolios"""

    __tablename__ = "positions"

    # id, portfolio_id, instrument_id, symbol fournis
    # par PortfolioInstrumentMixin
    # created_at, updated_at fournis par TimestampMixin
    quantity = Column(Numeric(15, 8), nullable=False)
    average_price = Column(Numeric(15, 4), nullable=False)
    market_price = Column(Numeric(15, 4))
    market_value = Column(Numeric(15, 4))
    book_value = Column(Numeric(15, 4))
    unrealized_pnl = Column(Numeric(15, 4), default=Decimal("0.0000"))
    unrealized_pnl_pct = Column(Numeric(8, 4), default=Decimal("0.0000"))
    realized_pnl = Column(Numeric(15, 4), default=Decimal("0.0000"))
    weight_pct = Column(Numeric(5, 2), default=Decimal("0.00"))
    first_purchase_date = Column(TIMESTAMP)
    last_transaction_date = Column(TIMESTAMP)
    is_active = Column(Boolean, default=True)

    # Relations
    portfolio = relationship("Portfolio", back_populates="positions")
    instrument = relationship("Instrument", back_populates="positions")

    __table_args__ = (
        UniqueConstraint("portfolio_id", "symbol", name="uq_portfolio_symbol"),
        Index("idx_positions_portfolio", "portfolio_id"),
        Index("idx_positions_symbol", "symbol"),
        Index("idx_positions_active", "is_active"),
    )

    def calculate_unrealized_pnl(self, current_price: Optional[float] = None):
        """Calculates unrealized profit or loss"""
        if current_price is None:
            current_price = float(self.market_price or 0)

        market_value = float(self.quantity) * current_price
        book_value = float(self.quantity) * float(self.average_price)
        return market_value - book_value

    def calculate_return_percentage(self, current_price: Optional[float] = None):
        """Calculates return percentage"""
        if current_price is None:
            current_price = float(self.market_price or 0)

        if self.average_price == 0:
            return 0.0

        return (
            (current_price - float(self.average_price)) / float(self.average_price)
        ) * 100
