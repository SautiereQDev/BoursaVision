"""
Domain Event Handlers
=====================

Handlers for domain events to implement cross-cutting concerns.
"""

from .event_handlers import (
    InvestmentAddedEventHandler,
    InvestmentCreatedEventHandler,
    PerformanceCalculatedEventHandler,
    PortfolioCreatedEventHandler,
    SignalGeneratedEventHandler,
)

__all__ = [
    "PortfolioCreatedEventHandler",
    "InvestmentAddedEventHandler",
    "InvestmentCreatedEventHandler",
    "SignalGeneratedEventHandler",
    "PerformanceCalculatedEventHandler",
]
