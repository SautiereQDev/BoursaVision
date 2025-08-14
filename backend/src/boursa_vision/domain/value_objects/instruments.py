"""
Domain value objects for financial instruments.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Stock:
    """Represents a stock instrument."""

    symbol: str
    name: str
    exchange: Optional[str] = None
    currency: str = "USD"

    def __str__(self) -> str:
        return f"{self.symbol} ({self.name})"


@dataclass(frozen=True)
class Bond:
    """Represents a bond instrument."""

    symbol: str
    name: str
    maturity_date: str
    coupon_rate: Decimal
    currency: str = "USD"


@dataclass(frozen=True)
class ETF:
    """Represents an ETF instrument."""

    symbol: str
    name: str
    expense_ratio: Decimal
    currency: str = "USD"
