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
    "InvestmentAddedEventHandler",
    "InvestmentCreatedEventHandler",
    "PerformanceCalculatedEventHandler",
    "PortfolioCreatedEventHandler",
    "SignalGeneratedEventHandler",
]
