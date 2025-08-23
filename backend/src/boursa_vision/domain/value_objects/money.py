"""
Value Objects for Monetary Operations
=====================================

Defines classes and constants for handling monetary values and currencies.

Classes:
    Currency: Enum representing supported currencies with metadata.
    Money: Represents a monetary amount with currency and operations.
"""

import re
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

# Constants
_CURRENCY_COMPARISON_ERROR = "Cannot compare different currencies"


class Currency(str, Enum):
    """Supported currencies with metadata"""

    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    CAD = "CAD"
    JPY = "JPY"
    CHF = "CHF"
    AUD = "AUD"

    @property
    def symbol(self) -> str:
        """Currency symbol"""
        symbols = {
            "USD": "$",
            "EUR": "€",
            "GBP": "£",
            "CAD": "C$",
            "JPY": "¥",
            "CHF": "Fr",
            "AUD": "A$",
        }
        return symbols.get(self.value, self.value)

    @property
    def decimal_places(self) -> int:
        """Number of decimal places for this currency,
        it has a very low value"""
        return 0 if self == Currency.JPY else 2

    @property
    def names(self) -> str:
        """English names of the currencies"""
        currencies = {
            "USD": "US Dollar",
            "EUR": "Euro",
            "GBP": "British Pound",
            "CAD": "Canadian Dollar",
            "JPY": "Japanese Yen",
            "CHF": "Swiss Franc",
            "AUD": "Australian Dollar",
        }
        return currencies.get(self.value, self.value)


@dataclass(frozen=True)
class Money:
    """
    Value Object representing a monetary amount.

    Characteristics:
    - Exact decimal precision
    - Currency validation
    - Safe arithmetic operations
    - Automatic rounding
    """

    amount: Decimal
    currency: Currency

    def __post_init__(self):
        """Validation upon creation"""
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))

        # Round according to currency
        rounded_amount = self.amount.quantize(
            Decimal("0.01") if self.currency != Currency.JPY else Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
        object.__setattr__(self, "amount", rounded_amount)

        # Validate amount
        if self.amount < 0:
            raise ValueError(f"Amount cannot be negative: {self.amount}")

        if abs(self.amount) > Decimal("999999999999.99"):
            raise ValueError(f"Amount too large: {self.amount}")

    @classmethod
    def zero(cls, currency: Currency) -> "Money":
        """Create a zero amount in the specified currency"""
        return cls(Decimal("0"), currency)

    @classmethod
    def from_float(cls, amount: float, currency: Currency) -> "Money":
        """Create from a float (with caution)"""
        return cls(Decimal(str(amount)), currency)

    @classmethod
    def from_string(cls, amount_str: str, currency: Currency) -> "Money":
        """Create from a string"""
        # Clean the string (remove spaces, commas)
        cleaned = re.sub(r"[^\d.-]", "", amount_str)
        return cls(Decimal(cleaned), currency)

    def __add__(self, other: "Money") -> "Money":
        """Add amounts (same currency)"""
        if not isinstance(other, Money):
            raise TypeError("Can only add Money to Money")

        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")

        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        """Subtract amounts"""
        if not isinstance(other, Money):
            raise TypeError("Can only subtract Money from Money")

        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {other.currency} from {self.currency}")

        result_amount = self.amount - other.amount
        if result_amount < 0:
            raise ValueError("Negative result not allowed")

        return Money(result_amount, self.currency)

    def __mul__(self, multiplier: Decimal) -> "Money":
        """Multiply by a factor"""
        if not isinstance(multiplier, (Decimal, int, float)):
            raise TypeError("Multiplier must be numeric")

        multiplier_decimal = Decimal(str(multiplier))
        return Money(self.amount * multiplier_decimal, self.currency)

    def __truediv__(self, divisor: Decimal) -> "Money":
        """Divide by a factor"""
        if not isinstance(divisor, (Decimal, int, float)):
            raise TypeError("Divisor must be numeric")

        divisor_decimal = Decimal(str(divisor))
        if divisor_decimal == 0:
            raise ZeroDivisionError("Cannot divide by zero")

        return Money(self.amount / divisor_decimal, self.currency)

    def __lt__(self, other: "Money") -> bool:
        """Less than comparison"""
        if self.currency != other.currency:
            raise ValueError(_CURRENCY_COMPARISON_ERROR)
        return self.amount < other.amount

    def __le__(self, other: "Money") -> bool:
        """Less than or equal comparison"""
        if self.currency != other.currency:
            raise ValueError(_CURRENCY_COMPARISON_ERROR)
        return self.amount <= other.amount

    def __gt__(self, other: "Money") -> bool:
        """Greater than comparison"""
        if self.currency != other.currency:
            raise ValueError(_CURRENCY_COMPARISON_ERROR)
        return self.amount > other.amount

    def __ge__(self, other: "Money") -> bool:
        """Greater than or equal comparison"""
        if self.currency != other.currency:
            raise ValueError(_CURRENCY_COMPARISON_ERROR)
        return self.amount >= other.amount

    def convert_to(self, target_currency: Currency, exchange_rate: Decimal) -> "Money":
        """Convert to another currency"""
        if self.currency == target_currency:
            return self

        if exchange_rate <= 0:
            raise ValueError("Exchange rate must be positive")

        converted_amount = self.amount * exchange_rate
        return Money(converted_amount, target_currency)

    def is_zero(self) -> bool:
        """Check if the amount is zero"""
        return self.amount == 0

    def is_positive(self) -> bool:
        """Check if the amount is positive"""
        return self.amount > 0

    def percentage_of(self, total: "Money") -> Decimal:
        """Calculate the percentage of this amount relative to the total"""
        if self.currency != total.currency:
            raise ValueError(_CURRENCY_COMPARISON_ERROR)

        if total.amount == 0:
            return Decimal("0")

        return (self.amount / total.amount) * 100

    def format(
        self, include_symbol: bool = True, decimal_places: int | None = None
    ) -> str:
        """Format the amount for display"""
        places = decimal_places or self.currency.decimal_places

        # Format with thousand separators
        amount_str = f"{self.amount:,.{places}f}"

        if include_symbol:
            return f"{self.currency.symbol}{amount_str}"
        return f"{amount_str} {self.currency.value}"

    def to_dict(self) -> dict:
        """Serialization"""
        return {"amount": str(self.amount), "currency": self.currency.value}

    @classmethod
    def from_dict(cls, data: dict) -> "Money":
        """Deserialization"""
        return cls(amount=Decimal(data["amount"]), currency=Currency(data["currency"]))

    def __str__(self) -> str:
        return self.format()

    def __repr__(self) -> str:
        return f"Money(amount={self.amount}, currency={self.currency.value})"
