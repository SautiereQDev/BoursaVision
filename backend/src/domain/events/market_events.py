"""
Market Data Domain Events
========================

Domain events related to market data updates and operations.

Classes:
    MarketDataUpdatedEvent: Fired when market data is updated.
    MarketDataBatchUpdatedEvent: Fired when multiple market data points are updated.
"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import List
from uuid import UUID

from .portfolio_events import DomainEvent


@dataclass(kw_only=True)
class MarketDataUpdatedEvent(DomainEvent):
    """Event fired when market data is updated"""
    
    symbol: str
    timestamp: datetime
    price: Decimal
    volume: int
    source: str


@dataclass(kw_only=True)
class MarketDataBatchUpdatedEvent(DomainEvent):
    """Event fired when multiple market data points are updated"""
    
    symbols: List[str]
    count: int
    source: str


@dataclass(kw_only=True)
class MarketSessionOpenedEvent(DomainEvent):
    """Event fired when a market session opens"""
    
    market: str
    session_date: datetime


@dataclass(kw_only=True)
class MarketSessionClosedEvent(DomainEvent):
    """Event fired when a market session closes"""
    
    market: str
    session_date: datetime


@dataclass(kw_only=True)
class PriceAlertTriggeredEvent(DomainEvent):
    """Event fired when a price alert is triggered"""
    
    symbol: str
    alert_id: UUID
    trigger_price: Decimal
    current_price: Decimal
    alert_type: str
