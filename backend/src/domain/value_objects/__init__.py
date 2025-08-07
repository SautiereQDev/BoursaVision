"""
Value Objects for Domain Layer
=============================

Money, Price, Signal and other value objects used throughout the domain.
"""

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional
from datetime import datetime

from .base import ValueObject


@dataclass(frozen=True)
class Money(ValueObject):
    """Money value object with currency"""
    amount: Decimal
    currency: str
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency cannot be empty")
    
    def __add__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def __sub__(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)
    
    def __mul__(self, factor: Decimal) -> 'Money':
        return Money(self.amount * factor, self.currency)
    
    def __gt__(self, other: 'Money') -> bool:
        if self.currency != other.currency:
            raise ValueError("Cannot compare different currencies")
        return self.amount > other.amount


class SignalAction(Enum):
    """Signal action types"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Signal(ValueObject):
    """Investment signal value object"""
    symbol: str
    action: SignalAction
    confidence_score: float
    price_target: Optional[Money]
    amount: Optional[Money]
    rationale: str
    generated_at: datetime
    metadata: dict = None
    
    def __post_init__(self):
        if not 0.0 <= self.confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0 and 1")
        if not self.symbol:
            raise ValueError("Symbol cannot be empty")
