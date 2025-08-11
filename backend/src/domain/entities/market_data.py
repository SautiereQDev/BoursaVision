"""
Market Data Entity - Core Business Domain
========================================

Pure business logic for market data management following DDD principles.
No dependencies on external frameworks or infrastructure.

Classes:
    MarketData: Represents market data for a financial instrument.
    Timeframe: Enum representing different timeframes for market data.
    DataSource: Enum representing different data sources.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from ..events.market_events import MarketDataUpdatedEvent
from ..value_objects.money import Currency, Money
from ..value_objects.price import Price
from .base import AggregateRoot


class Timeframe(str, Enum):
    """Market data timeframes"""
    
    MINUTE_1 = "1m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_4 = "4h"
    DAY_1 = "1d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"

    @property
    def minutes(self) -> int:
        """Get timeframe in minutes"""
        timeframe_minutes = {
            self.MINUTE_1: 1,
            self.MINUTE_5: 5,
            self.MINUTE_15: 15,
            self.MINUTE_30: 30,
            self.HOUR_1: 60,
            self.HOUR_4: 240,
            self.DAY_1: 1440,
            self.WEEK_1: 10080,
            self.MONTH_1: 43200,  # Approximate
        }
        return timeframe_minutes.get(self, 1440)


class DataSource(str, Enum):
    """Market data sources"""
    
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    IEX_CLOUD = "iex_cloud"
    FINNHUB = "finnhub"
    POLYGON = "polygon"
    INTERNAL = "internal"

    @property
    def priority(self) -> int:
        """Source priority (lower number = higher priority)"""
        priorities = {
            self.INTERNAL: 1,
            self.POLYGON: 2,
            self.IEX_CLOUD: 3,
            self.ALPHA_VANTAGE: 4,
            self.YAHOO_FINANCE: 5,
            self.FINNHUB: 6,
        }
        return priorities.get(self, 99)


@dataclass
class MarketData(AggregateRoot):
    """
    Market data aggregate representing price and volume information
    for a financial instrument at a specific point in time.
    """
    
    id: UUID = field(default_factory=uuid4)
    symbol: str = field(default="")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    timeframe: Timeframe = field(default=Timeframe.DAY_1)
    source: DataSource = field(default=DataSource.YAHOO_FINANCE)
    currency: Currency = field(default=Currency.USD)
    
    # OHLCV data
    open_price: Decimal = field(default=Decimal("0"))
    high_price: Decimal = field(default=Decimal("0"))
    low_price: Decimal = field(default=Decimal("0"))
    close_price: Decimal = field(default=Decimal("0"))
    volume: int = field(default=0)
    
    # Additional market metrics
    adjusted_close: Optional[Decimal] = field(default=None)
    dividend_amount: Optional[Decimal] = field(default=None)
    split_coefficient: Optional[Decimal] = field(default=None)
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Initialize aggregate root and validate market data"""
        super().__init__()
        self._validate()
    
    @classmethod
    def create(
        cls,
        symbol: str,
        timestamp: datetime,
        open_price: Decimal,
        high_price: Decimal,
        low_price: Decimal,
        close_price: Decimal,
        volume: int,
        timeframe: Timeframe = Timeframe.DAY_1,
        source: DataSource = DataSource.YAHOO_FINANCE,
        currency: Currency = Currency.USD,
        adjusted_close: Optional[Decimal] = None,
        dividend_amount: Optional[Decimal] = None,
        split_coefficient: Optional[Decimal] = None
    ) -> "MarketData":
        """Factory method to create market data"""
        market_data = cls(
            symbol=symbol,
            timestamp=timestamp,
            timeframe=timeframe,
            source=source,
            currency=currency,
            open_price=open_price,
            high_price=high_price,
            low_price=low_price,
            close_price=close_price,
            volume=volume,
            adjusted_close=adjusted_close,
            dividend_amount=dividend_amount,
            split_coefficient=split_coefficient
        )
        
        market_data._add_domain_event(MarketDataUpdatedEvent(
            symbol=symbol,
            timestamp=timestamp,
            price=close_price,
            volume=volume,
            source=source.value
        ))
        
        return market_data
    
    def _validate(self) -> None:
        """Validate market data business rules"""
        if not self.symbol:
            raise ValueError("Symbol is required")
            
        if len(self.symbol) > 10:
            raise ValueError("Symbol too long (max 10 characters)")
            
        if self.open_price <= 0:
            raise ValueError("Open price must be positive")
            
        if self.high_price <= 0:
            raise ValueError("High price must be positive")
            
        if self.low_price <= 0:
            raise ValueError("Low price must be positive")
            
        if self.close_price <= 0:
            raise ValueError("Close price must be positive")
            
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")
            
        # OHLC validation
        if self.high_price < self.low_price:
            raise ValueError("High price cannot be lower than low price")
            
        if self.high_price < self.open_price:
            raise ValueError("High price cannot be lower than open price")
            
        if self.high_price < self.close_price:
            raise ValueError("High price cannot be lower than close price")
            
        if self.low_price > self.open_price:
            raise ValueError("Low price cannot be higher than open price")
            
        if self.low_price > self.close_price:
            raise ValueError("Low price cannot be higher than close price")
    
    def update_prices(
        self,
        open_price: Decimal,
        high_price: Decimal,
        low_price: Decimal,
        close_price: Decimal,
        volume: int,
        adjusted_close: Optional[Decimal] = None
    ) -> None:
        """Update market data prices"""
        self.open_price = open_price
        self.high_price = high_price
        self.low_price = low_price
        self.close_price = close_price
        self.volume = volume
        self.adjusted_close = adjusted_close
        self.updated_at = datetime.now(timezone.utc)
        
        self._validate()
        
        self._add_domain_event(MarketDataUpdatedEvent(
            symbol=self.symbol,
            timestamp=self.timestamp,
            price=close_price,
            volume=volume,
            source=self.source.value
        ))
    
    def get_typical_price(self) -> Decimal:
        """Calculate typical price (HLC/3)"""
        return (self.high_price + self.low_price + self.close_price) / Decimal("3")
    
    def get_weighted_price(self) -> Decimal:
        """Calculate weighted price (OHLC/4)"""
        return (
            self.open_price + self.high_price + 
            self.low_price + self.close_price
        ) / Decimal("4")
    
    def get_price_change(self) -> Decimal:
        """Calculate price change (close - open)"""
        return self.close_price - self.open_price
    
    def get_price_change_percent(self) -> Decimal:
        """Calculate price change percentage"""
        if self.open_price == 0:
            return Decimal("0")
        return (self.get_price_change() / self.open_price) * Decimal("100")
    
    def get_price_range(self) -> Decimal:
        """Calculate price range (high - low)"""
        return self.high_price - self.low_price
    
    def get_price_range_percent(self) -> Decimal:
        """Calculate price range as percentage of open"""
        if self.open_price == 0:
            return Decimal("0")
        return (self.get_price_range() / self.open_price) * Decimal("100")
    
    def get_price(self, price_type: str = "close") -> Price:
        """Get price as Price value object"""
        price_map = {
            "open": self.open_price,
            "high": self.high_price,
            "low": self.low_price,
            "close": self.close_price,
            "adjusted": self.adjusted_close or self.close_price,
            "typical": self.get_typical_price(),
            "weighted": self.get_weighted_price()
        }
        
        amount = price_map.get(price_type, self.close_price)
        return Price(
            amount=amount,
            currency=self.currency,
            timestamp=self.timestamp,
            symbol=self.symbol
        )
    
    def is_gap_up(self, threshold_percent: Decimal = Decimal("2")) -> bool:
        """Check if there's a gap up from previous close"""
        if self.adjusted_close is None:
            return False
        gap_percent = ((self.open_price - self.adjusted_close) / self.adjusted_close) * Decimal("100")
        return gap_percent >= threshold_percent
    
    def is_gap_down(self, threshold_percent: Decimal = Decimal("2")) -> bool:
        """Check if there's a gap down from previous close"""
        if self.adjusted_close is None:
            return False
        gap_percent = ((self.adjusted_close - self.open_price) / self.adjusted_close) * Decimal("100")
        return gap_percent >= threshold_percent
    
    def has_dividend(self) -> bool:
        """Check if this period has a dividend"""
        return self.dividend_amount is not None and self.dividend_amount > 0
    
    def has_split(self) -> bool:
        """Check if this period has a stock split"""
        return (
            self.split_coefficient is not None and 
            self.split_coefficient != Decimal("1")
        )
    
    def __str__(self) -> str:
        return f"MarketData({self.symbol}, {self.timestamp.date()}, ${self.close_price})"
    
    def __repr__(self) -> str:
        return (
            f"MarketData(symbol='{self.symbol}', "
            f"timestamp={self.timestamp}, "
            f"close_price={self.close_price}, "
            f"volume={self.volume})"
        )
