"""
Domain Events for Portfolio Operations

Events that occur within the portfolio domain for CQRS and event sourcing.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from ..entities.base import DomainEvent

if TYPE_CHECKING:
    from ..entities.investment import InvestmentSector, InvestmentType
    from ..value_objects import Money, Signal


@dataclass
class PortfolioCreatedEvent(DomainEvent):
    """Event raised when a new portfolio is created"""

    portfolio_id: UUID
    user_id: UUID
    name: str
    timestamp: datetime


@dataclass
class InvestmentAddedEvent(DomainEvent):
    """Event raised when an investment is added to portfolio"""

    portfolio_id: UUID
    symbol: str
    quantity: int
    price: "Money"
    timestamp: datetime


@dataclass
class InvestmentCreatedEvent(DomainEvent):
    """Event raised when a new investment is created"""

    investment_id: UUID
    symbol: str
    name: str
    investment_type: "InvestmentType"
    sector: "InvestmentSector"


@dataclass  # pylint: disable=too-many-instance-attributes
class InvestmentAnalyzedEvent(DomainEvent):
    """Event raised when an investment analysis is completed"""

    investment_id: UUID
    symbol: str
    composite_score: float
    signal: "Signal"


@dataclass
class PortfolioRebalancedEvent(DomainEvent):
    """Event raised when portfolio is rebalanced"""

    portfolio_id: UUID
    user_id: UUID
    old_allocation: dict  # symbol -> percentage
    new_allocation: dict  # symbol -> percentage
    rebalance_reason: str


@dataclass
class RiskLimitExceededEvent(DomainEvent):
    """Event raised when risk limits are exceeded"""

    portfolio_id: UUID
    user_id: UUID
    risk_type: str  # "position_limit", "sector_exposure", "daily_loss"
    current_value: float
    limit_value: float
    symbol: Optional[str] = None


@dataclass
class PositionUpdatedEvent(DomainEvent):
    """Event raised when a position is updated"""

    portfolio_id: UUID
    symbol: str
    old_quantity: int
    new_quantity: int
    average_price: "Money"
    update_reason: str  # "buy", "sell", "dividend", "split"


@dataclass
class PerformanceCalculatedEvent(DomainEvent):  # pylint: disable=too-many-instance-attributes
    """Event raised when portfolio performance is calculated"""

    portfolio_id: UUID
    user_id: UUID
    total_value: "Money"
    daily_return: float
    monthly_return: float
    annual_return: float
    sharpe_ratio: float
    calculation_date: datetime
