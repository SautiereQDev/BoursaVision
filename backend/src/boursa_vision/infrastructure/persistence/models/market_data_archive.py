"""Market data archiving models for time series data."""

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Index,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.sql import func

from .base import Base


class MarketDataArchive(Base):
    """
    Market data archive for storing historical financial data.

    This model stores market data with TimescaleDB hypertable optimization
    for efficient time-series queries and data compression.
    """

    __tablename__ = "market_data_archive"

    id = Column("id", nullable=False, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    open_price = Column(Numeric(20, 8), nullable=True)
    high_price = Column(Numeric(20, 8), nullable=True)
    low_price = Column(Numeric(20, 8), nullable=True)
    close_price = Column(Numeric(20, 8), nullable=True)
    volume = Column(BigInteger, nullable=True)
    interval_type = Column(String(10), nullable=False, server_default="1d")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Ensure uniqueness per symbol, timestamp, and interval
    __table_args__ = (
        UniqueConstraint(
            "symbol", "timestamp", "interval_type", name="uix_symbol_timestamp_interval"
        ),
        Index("idx_market_data_archive_symbol_timestamp", "symbol", "timestamp"),
    )

    def __repr__(self) -> str:
        """String representation of MarketDataArchive."""
        return (
            f"<MarketDataArchive("
            f"symbol='{self.symbol}', "
            f"timestamp='{self.timestamp}', "
            f"close_price={self.close_price}, "
            f"interval='{self.interval_type}'"
            f")>"
        )

    @classmethod
    def create_from_yfinance(cls, symbol: str, data_row, interval: str = "1d"):
        """
        Create MarketDataArchive instance from YFinance data.

        Args:
            symbol: Financial symbol (e.g., 'AAPL', 'BTC-USD')
            data_row: YFinance data row with OHLCV data
            interval: Data interval ('1m', '5m', '1h', '1d', etc.)

        Returns:
            MarketDataArchive instance
        """
        return cls(
            symbol=symbol,
            timestamp=data_row.name
            if hasattr(data_row, "name")
            else data_row["timestamp"],
            open_price=float(data_row["Open"])
            if data_row["Open"] is not None
            else None,
            high_price=float(data_row["High"])
            if data_row["High"] is not None
            else None,
            low_price=float(data_row["Low"]) if data_row["Low"] is not None else None,
            close_price=float(data_row["Close"])
            if data_row["Close"] is not None
            else None,
            volume=int(data_row["Volume"]) if data_row["Volume"] is not None else None,
            interval_type=interval,
        )
