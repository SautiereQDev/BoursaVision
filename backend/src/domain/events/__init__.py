"""
Domain events package.

Contains event classes for the domain.
"""

from .portfolio_events import DomainEvent, InvestmentAddedEvent, PortfolioCreatedEvent
from .market_events import (
    MarketDataBatchUpdatedEvent,
    MarketDataUpdatedEvent,
    MarketSessionClosedEvent,
    MarketSessionOpenedEvent,
    PriceAlertTriggeredEvent,
)
from .user_events import (
    UserCreatedEvent,
    UserDeactivatedEvent,
    UserEmailVerifiedEvent,
    UserRoleChangedEvent,
    UserTwoFactorEnabledEvent,
)

__all__ = [
    "DomainEvent",
    "PortfolioCreatedEvent",
    "InvestmentAddedEvent",
    "UserCreatedEvent",
    "UserDeactivatedEvent",
    "UserEmailVerifiedEvent",
    "UserRoleChangedEvent",
    "UserTwoFactorEnabledEvent",
    "MarketDataUpdatedEvent",
    "MarketDataBatchUpdatedEvent",
    "MarketSessionOpenedEvent",
    "MarketSessionClosedEvent",
    "PriceAlertTriggeredEvent",
]
