"""
Domain Events for Portfolio Operations
=====================================

Events that occur within the portfolio domain for CQRS and event sourcing.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ..entities.base import DomainEvent
from ..value_objects import Money


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
    price: Money
    timestamp: datetime
