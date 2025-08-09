"""
Value Object for Financial Prices
=================================

Defines the `Price` class for representing financial asset prices with
validation and domain-specific operations.

Classes:
    Price: Represents the price of a financial asset with
    currency and timestamp.
"""

import statistics
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterator, List, Optional

from .money import Currency, Money


@dataclass(frozen=True)
class Price:
    """
    Value Object representing a financial asset price.

    Specialized for financial data with validation
    and specific business operations.
    """

    value: Decimal
    currency: Currency
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Validation specific to financial prices"""
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, "value", Decimal(str(self.value)))

        if self.value < 0:
            raise ValueError("Price cannot be negative")

        if self.value > Decimal("999999.9999"):
            raise ValueError("Price too high")

        # Maximum precision of 4 decimal places for prices
        rounded_value = self.value.quantize(Decimal("0.0001"))
        object.__setattr__(self, "value", rounded_value)

    @classmethod
    def from_float(
        cls,
        value: float,
        currency: Currency,
        timestamp: Optional[datetime] = None,
    ) -> "Price":
        """Création depuis un float"""
        return cls(Decimal(str(value)), currency, timestamp)

    def to_money(self, quantity: Decimal) -> Money:
        """Convert to amount for a given quantity"""
        total_amount = self.value * quantity
        return Money(total_amount, self.currency)

    def change_from(self, previous_price: "Price") -> Decimal:
        """Calculate absolute change from a previous price"""
        if self.currency != previous_price.currency:
            raise ValueError("Cannot compare prices in different currencies")

        return self.value - previous_price.value

    def change_percentage_from(self, previous_price: "Price") -> Decimal:
        """Calculate percentage change"""
        if previous_price.value == 0:
            return Decimal("0")

        change = self.change_from(previous_price)
        return (change / previous_price.value) * 100

    def is_higher_than(self, other_price: "Price") -> bool:
        """Compare if this price is higher"""
        if self.currency != other_price.currency:
            raise ValueError("Cannot compare prices in different currencies")

        return self.value > other_price.value

    def format(self, include_currency: bool = True) -> str:
        """Format the price for display"""
        formatted = f"{self.value:.4f}".rstrip("0").rstrip(".")

        if include_currency:
            return f"{formatted} {self.currency.value}"

        return formatted

    def __str__(self) -> str:
        return self.format()


@dataclass(frozen=True)
class PricePoint:

    @property
    def currency(self) -> Currency:
        """Return the currency (all prices are validated to be the same)."""
        return self.open_price.currency
    """Point de données OHLCV (Open, High, Low, Close, Volume)"""

    timestamp: datetime
    open_price: Price
    high_price: Price
    low_price: Price
    close_price: Price
    volume: int
    adjusted_close: Optional[Price] = None

    def __post_init__(self):
        """OHLC consistency validation"""
        prices = [
            self.open_price,
            self.high_price,
            self.low_price,
            self.close_price,
        ]

        self._validate_currencies(prices)
        self._validate_ohlc_logic()
        self._validate_volume()

    def _validate_currencies(self, prices: List["Price"]) -> None:
        currencies = {p.currency for p in prices}
        if len(currencies) > 1:
            raise ValueError("All prices must be in the same currency")

    def _validate_ohlc_logic(self) -> None:
        if not (self.low_price.value <= self.open_price.value
                <= self.high_price.value):
            raise ValueError("Invalid OHLC: open price not between"
                             "high and low")

        if not (self.low_price.value <= self.close_price.value
                <= self.high_price.value):
            raise ValueError("Invalid OHLC: close price not between"
                             "high and low")

    def _validate_volume(self) -> None:
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

    @property
    def price_range(self) -> Decimal:
        """Écart entre high et low"""
        return self.high_price.value - self.low_price.value

    @property
    def price_change(self) -> Decimal:
        """Changement entre open et close"""
        return self.close_price.value - self.open_price.value

    @property
    def price_change_percentage(self) -> Decimal:
        """Changement en pourcentage"""
        if self.open_price.value == 0:
            return Decimal("0")

        return (self.price_change / self.open_price.value) * 100

    def is_bullish(self) -> bool:
        """Check if the candle is bullish"""
        return self.close_price.value > self.open_price.value

    def is_bearish(self) -> bool:
        """Check if the candle is bearish"""
        return self.close_price.value < self.open_price.value

    def is_doji(self, threshold_pct: Decimal = Decimal("0.1")) -> bool:
        """Check if it's a doji (open ≈ close)"""
        if self.open_price.value == 0:
            return False

        change_pct = abs(self.price_change_percentage)
        return change_pct <= threshold_pct


@dataclass(frozen=True)
class PriceData:
    """Collection of price points with analysis methods"""

    symbol: str
    points: List[PricePoint]
    interval: str  # 1d, 1h, 5m, etc.

    def __post_init__(self):
        """Price series validation"""
        if not self.points:
            raise ValueError("Price data cannot be empty")

        if not self.symbol:
            raise ValueError("Symbol is required")

        # Check chronological order
        timestamps = [point.timestamp for point in self.points]
        if timestamps != sorted(timestamps):
            raise ValueError("Price points must be in chronological order")

        # Check currency consistency
        currencies = {point.open_price.currency for point in self.points}
        if len(currencies) > 1:
            raise ValueError("All price points must be in the same currency")

    @property
    def currency(self) -> Currency:
        """Data currency"""
        return self.points[0].open_price.currency

    @property
    def latest_price(self) -> Price:
        """Dernier prix de clôture"""
        return self.points[-1].close_price

    @property
    def oldest_price(self) -> Price:
        """Premier prix de clôture"""
        return self.points[0].close_price

    @property
    def period_return(self) -> Decimal:
        """Rendement sur la période"""
        if len(self.points) < 2:
            return Decimal("0")

        return self.latest_price.change_percentage_from(self.oldest_price)

    @property
    def highest_price(self) -> Price:
        """Prix le plus haut de la période"""
        return max(self.points, key=lambda p: p.high_price.value).high_price

    @property
    def lowest_price(self) -> Price:
        """Prix le plus bas de la période"""
        return min(self.points, key=lambda p: p.low_price.value).low_price

    @property
    def average_volume(self) -> int:
        """Volume moyen"""
        return int(statistics.mean(point.volume for point in self.points))

    @property
    def total_volume(self) -> int:
        """Volume total"""
        return sum(point.volume for point in self.points)

    def get_closing_prices(self) -> List[Decimal]:
        """Extrait la série des prix de clôture"""
        return [point.close_price.value for point in self.points]

    def get_returns(self) -> List[Decimal]:
        """Calculate the series of daily returns"""
        closes = self.get_closing_prices()
        if len(closes) < 2:
            return []

        returns = []
        for i in range(1, len(closes)):
            if closes[i - 1] != 0:
                daily_return = (closes[i] - closes[i - 1]) / closes[i - 1]
                returns.append(daily_return)

        return returns

    def calculate_volatility(self) -> Decimal:
        """Calculate volatility (standard deviation of returns)"""
        returns = self.get_returns()
        if len(returns) < 2:
            return Decimal("0")

        return Decimal(str(statistics.stdev(returns)))

    def get_price_at_date(self, target_date: date) -> Optional[Price]:
        """Trouve le prix à une date donnée"""
        for point in self.points:
            if point.timestamp.date() == target_date:
                return point.close_price

        return None

    def slice_by_date(self, start_date: date, end_date: date) -> "PriceData":
        """Découpe les données entre deux dates"""
        filtered_points = [
            point
            for point in self.points
            if start_date <= point.timestamp.date() <= end_date
        ]

        return PriceData(self.symbol, filtered_points, self.interval)

    def __len__(self) -> int:
        return len(self.points)

    def __iter__(self) -> Iterator[PricePoint]:
        return iter(self.points)

    def __getitem__(self, index: int) -> PricePoint:
        return self.points[index]
