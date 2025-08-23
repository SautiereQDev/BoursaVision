"""
Domain entities package.

Contains aggregate roots and entities for the domain.
"""

from .base import AggregateRoot, DomainEvent, Entity
from .investment import Investment
from .market_data import DataSource, MarketData, Timeframe
from .portfolio import Portfolio, Position
from .user import User, UserRole

__all__ = [
    "AggregateRoot",
    "DataSource",
    "DomainEvent",
    "Entity",
    "Investment",
    "MarketData",
    "Portfolio",
    "Position",
    "Timeframe",
    "User",
    "UserRole",
]

from .investment import (
    AnalysisDataMissingError,
    FundamentalData,
    InvestmentSector,
    InvestmentType,
    InvestmentValidationException,
    MarketCap,
    TechnicalData,
)
from .portfolio import (
    InsufficientFundsError,
    PerformanceMetrics,
    PositionLimitExceededError,
    RiskLimits,
)

__all__ = [
    "AggregateRoot",
    "AnalysisDataMissingError",
    "DomainEvent",
    "FundamentalData",
    "InsufficientFundsError",
    # Investment entities
    "Investment",
    "InvestmentSector",
    "InvestmentType",
    "InvestmentValidationException",
    "MarketCap",
    "PerformanceMetrics",
    "Portfolio",
    # Portfolio entities
    "Position",
    "PositionLimitExceededError",
    "RiskLimits",
    "TechnicalData",
]
