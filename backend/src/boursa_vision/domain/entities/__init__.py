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
    "DomainEvent",
    "Entity",
    "Investment",
    "Portfolio",
    "Position",
    "User",
    "UserRole",
    "MarketData",
    "Timeframe",
    "DataSource",
]

from .investment import (
    AnalysisDataMissingException,
    FundamentalData,
    InvestmentSector,
    InvestmentType,
    InvestmentValidationException,
    MarketCap,
    TechnicalData,
)
from .portfolio import (
    InsufficientFundsException,
    PerformanceMetrics,
    PositionLimitExceededException,
    RiskLimits,
)

__all__ = [
    "AggregateRoot",
    "DomainEvent",
    # Investment entities
    "Investment",
    "InvestmentType",
    "InvestmentSector",
    "MarketCap",
    "FundamentalData",
    "TechnicalData",
    "InvestmentValidationException",
    "AnalysisDataMissingException",
    # Portfolio entities
    "Position",
    "RiskLimits",
    "PerformanceMetrics",
    "Portfolio",
    "InsufficientFundsException",
    "PositionLimitExceededException",
]
