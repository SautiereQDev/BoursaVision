"""
Domain entities package.

This package contains the core domain entity classes.

Modules:
    base: Base classes for domain entities and aggregate roots.
    portfolio: Portfolio entity with its business logic.
    investment: Investment entity with analysis capabilities.
"""

from .base import AggregateRoot, DomainEvent
from .investment import (
    AnalysisDataMissingException,
    FundamentalData,
    Investment,
    InvestmentSector,
    InvestmentType,
    InvestmentValidationException,
    MarketCap,
    TechnicalData,
)
from .portfolio import (
    InsufficientFundsException,
    PerformanceMetrics,
    Portfolio,
    Position,
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
