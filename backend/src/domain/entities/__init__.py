"""
Domain entities package.

This package contains the core domain entity classes.

Modules:
    base: Base classes for domain entities and aggregate roots.
    portfolio: Portfolio entity with its business logic.
"""

from .base import AggregateRoot, DomainEvent
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
    "Position",
    "RiskLimits",
    "PerformanceMetrics",
    "Portfolio",
    "InsufficientFundsException",
    "PositionLimitExceededException",
]
