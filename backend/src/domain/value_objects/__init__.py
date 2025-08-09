"""
Value Objects for the financial domain.

Value Objects are immutable objects that represent business concepts
by their value rather than their identity.

Characteristics:
- Immutable (frozen dataclass)
- Equality by value
- No unique identity
- Integrated business validation
"""

from .money import Currency, Money
from .price import Price
from .signal import ConfidenceScore, Signal, SignalAction, SignalStrength

__all__ = [
    "Money",
    "Currency",
    "Price",
    "Signal",
    "SignalAction",
    "SignalStrength",
    "ConfidenceScore",
]
