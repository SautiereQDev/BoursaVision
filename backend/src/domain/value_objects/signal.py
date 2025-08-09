"""
Signal Module
=============

This module defines value objects related to investment signals, including
their actions, strengths, confidence scores, and associated metadata.

Classes:
    SignalAction: Represents the recommended action for an investment signal.
    SignalStrength: Represents the strength of an investment signal.
    ConfidenceScore: Represents a normalized confidence score between 0 and 1.
    Signal: Represents an investment signal with associated metadata.
"""

from dataclasses import dataclass, replace
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional

from .money import Currency
from .price import Price


class SignalAction(str, Enum):
    """Recommended action for the signal"""

    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

    @property
    def label_en(self) -> str:
        """
        Returns the English label corresponding to the signal's value.

        The method maps the signal's value to its English representation
        using a predefined dictionary of labels.

        Returns:
            str: The English label for the signal's value.

        Raises:
            KeyError: If the signal's value is not found in the
            labels dictionary.
        """
        labels = {"BUY": "Buy", "SELL": "Sell", "HOLD": "Hold"}
        return labels[self.value]

    @property
    def color(self) -> str:
        """Color for the interface"""
        colors = {"BUY": "green", "SELL": "red", "HOLD": "gray"}
        return colors[self.value]


# Adjust SignalStrength thresholds to match test expectations
class SignalStrength(str, Enum):
    """Strength of the signal"""

    WEAK = "WEAK"
    MODERATE = "MODERATE"
    STRONG = "STRONG"

    @property
    def label_en(self) -> str:
        """
        Returns the English label corresponding to the current signal value.

        The method maps the signal's value to a predefined English label
        based on its intensity level.

        Returns:
            str: The English label for the signal value. Possible values are
            "Weak", "Moderate", or "Strong".

        Raises:
            KeyError: If the signal value is not one of the predefined keys
            ("WEAK", "MODERATE", "STRONG").
        """
        labels = {"WEAK": "Weak", "MODERATE": "Moderate", "STRONG": "Strong"}
        return labels[self.value]

    @property
    def min_confidence(self) -> Decimal:
        """Minimum confidence score for this strength"""
        thresholds = {
            "WEAK": Decimal("0.3"),
            "MODERATE": Decimal("0.5"),  # Adjusted threshold for MODERATE
            "STRONG": Decimal("0.7"),  # Adjusted threshold for STRONG
        }
        return thresholds[self.value]


@dataclass(frozen=True)
class ConfidenceScore:
    """Normalized confidence score between 0 and 1"""

    value: Decimal

    def __post_init__(self):
        """Validate the score"""
        if not isinstance(self.value, Decimal):
            object.__setattr__(self, "value", Decimal(str(self.value)))

        if not Decimal("0") <= self.value <= Decimal("1"):
            raise ValueError("Confidence score must be between 0 and 1")

        # Round to 2 decimal places
        rounded_value = self.value.quantize(Decimal("0.01"))
        object.__setattr__(self, "value", rounded_value)

    @classmethod
    def from_percentage(cls, percentage: float) -> "ConfidenceScore":
        """Create from a percentage (0-100)"""
        return cls(Decimal(str(percentage)) / 100)

    @property
    def strength(self) -> SignalStrength:
        """Determine the strength based on the score"""
        if self.value >= Decimal("0.7"):  # Adjusted threshold for STRONG
            return SignalStrength.STRONG
        if self.value >= Decimal("0.5"):  # Adjusted threshold for MODERATE
            return SignalStrength.MODERATE

        # Below 0.5 is weak
        return SignalStrength.WEAK

    @property
    def percentage(self) -> Decimal:
        """Return as a percentage"""
        return self.value * 100

    def is_high(self) -> bool:
        """Check if the score is high (>= 0.7)"""
        return self.value >= Decimal("0.7")

    def is_reliable(self) -> bool:
        """Check if the signal is reliable (>= 0.6)"""
        return self.value >= Decimal("0.6")

    def format(self) -> str:
        """Format for display"""
        return f"{self.percentage:.0f}%"

    def __str__(self) -> str:
        return self.format()


@dataclass(frozen=True)
# pylint: disable=too-many-instance-attributes
class Signal:
    """
    Value Object representing an investment signal.

    Combines action, confidence, target prices, and rationale
    for a complete recommendation.
    """

    symbol: str
    action: SignalAction
    confidence_score: ConfidenceScore
    generated_at: datetime
    price_target: Optional[Price] = None
    stop_loss: Optional[Price] = None
    rationale: Optional[str] = None
    technical_score: Optional[Decimal] = None
    fundamental_score: Optional[Decimal] = None
    market_context_score: Optional[Decimal] = None
    indicators_used: Optional[List[str]] = None
    metadata: Optional[Dict] = None
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate the signal"""
        if not self.symbol:
            raise ValueError("Symbol is required")

        # Validate price consistency
        if self.price_target and self.stop_loss:
            self._validate_price_consistency()

        # Validate expiration
        if self.expires_at and self.expires_at <= self.generated_at:
            raise ValueError("Expiry date must be after generation date")

        # Initialize empty metadata if None
        self._initialize_metadata()

    def _validate_price_consistency(self):
        """Helper to validate price consistency"""
        if self.action == SignalAction.BUY:
            # For a buy: price_target > stop_loss
            if self.price_target.value <= self.stop_loss.value:
                raise ValueError("For BUY signal: price_target must be > stop_loss")
        elif self.action == SignalAction.SELL:
            # For a sell: stop_loss > price_target
            if self.stop_loss.value <= self.price_target.value:
                raise ValueError("For SELL signal: stop_loss must be > price_target")

    def _initialize_metadata(self):
        """Helper to initialize metadata and indicators"""
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})

        if self.indicators_used is None:
            object.__setattr__(self, "indicators_used", [])

    @property
    def strength(self) -> SignalStrength:
        """Signal strength based on confidence score"""
        return self.confidence_score.strength

    @property
    def composite_score(self) -> Decimal:
        """Composite score calculated from sub-scores"""
        if not any(
            [
                self.technical_score,
                self.fundamental_score,
                self.market_context_score,
            ]
        ):
            return self.confidence_score.value

        # Weighting: technical 40%, fundamental 40%, context 20%
        technical = self.technical_score or Decimal("0")
        fundamental = self.fundamental_score or Decimal("0")
        context = self.market_context_score or Decimal("0")

        return (
            technical * Decimal("0.4")
            + fundamental * Decimal("0.4")
            + context * Decimal("0.2")
        )

    def is_valid(self) -> bool:
        """Check if the signal is still valid"""
        if self.expires_at is None:
            return True

        return datetime.now() < self.expires_at

    def is_actionable(self) -> bool:
        """Check if the signal justifies an action"""
        return self.confidence_score.is_reliable() and self.is_valid()

    def calculate_risk_reward_ratio(self, current_price: Price) -> Optional[Decimal]:
        """Calculate the risk/reward ratio"""
        if not (self.price_target and self.stop_loss):
            return None

        if self.action == SignalAction.BUY:
            potential_gain = self.price_target.value - current_price.value
            potential_loss = current_price.value - self.stop_loss.value
        elif self.action == SignalAction.SELL:
            potential_gain = current_price.value - self.price_target.value
            potential_loss = self.stop_loss.value - current_price.value
        else:
            return None

        if potential_loss <= 0:
            return None

        return potential_gain / potential_loss

    def get_potential_return_percentage(
        self, current_price: Price
    ) -> Optional[Decimal]:
        """Calculate the potential return percentage"""
        if not self.price_target or current_price.value == 0:
            return None

        if self.action == SignalAction.BUY:
            return (
                (self.price_target.value - current_price.value) / current_price.value
            ) * 100
        if self.action == SignalAction.SELL:
            return (
                (current_price.value - self.price_target.value) / current_price.value
            ) * 100

        return None

    def add_metadata(self, key: str, value) -> "Signal":
        """Add metadata (returns new signal)"""
        new_metadata = dict(self.metadata or {})
        new_metadata[key] = value

        return replace(self, metadata=new_metadata)

    def to_dict(self) -> Dict:
        """Serialization for storage/API"""
        return {
            "symbol": self.symbol,
            "action": self.action.value,
            "confidence_score": str(self.confidence_score.value),
            "strength": self.strength.value,
            "generated_at": self.generated_at.isoformat(),
            "price_target": (
                str(self.price_target.value) if self.price_target else None
            ),
            "stop_loss": (str(self.stop_loss.value) if self.stop_loss else None),
            "rationale": self.rationale,
            "technical_score": (
                str(self.technical_score) if self.technical_score else None
            ),
            "fundamental_score": (
                str(self.fundamental_score) if self.fundamental_score else None
            ),
            "market_context_score": (
                str(self.market_context_score) if self.market_context_score else None
            ),
            "indicators_used": self.indicators_used,
            "metadata": self.metadata,
            "expires_at": (self.expires_at.isoformat() if self.expires_at else None),
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Signal":
        """Deserialization from a dictionary"""
        return cls(
            symbol=data["symbol"],
            action=SignalAction(data["action"]),
            confidence_score=ConfidenceScore(Decimal(data["confidence_score"])),
            generated_at=datetime.fromisoformat(data["generated_at"]),
            price_target=(
                Price(Decimal(data["price_target"]), Currency.USD)
                if data.get("price_target")
                else None
            ),
            stop_loss=(
                Price(Decimal(data["stop_loss"]), Currency.USD)
                if data.get("stop_loss")
                else None
            ),
            rationale=data.get("rationale"),
            technical_score=(
                Decimal(data["technical_score"])
                if data.get("technical_score")
                else None
            ),
            fundamental_score=(
                Decimal(data["fundamental_score"])
                if data.get("fundamental_score")
                else None
            ),
            market_context_score=(
                Decimal(data["market_context_score"])
                if data.get("market_context_score")
                else None
            ),
            indicators_used=data.get("indicators_used", []),
            metadata=data.get("metadata", {}),
            expires_at=(
                datetime.fromisoformat(data["expires_at"])
                if data.get("expires_at")
                else None
            ),
        )

    def __str__(self) -> str:
        """String representation of the signal"""
        confidence_pct = f"{self.confidence_score.percentage:.0f}%"
        target_info = f" -> {self.price_target.value}" if self.price_target else ""
        return f"{self.action.value} {self.symbol} " f"({confidence_pct}){target_info}"

    def __repr__(self) -> str:
        """Debug representation of the signal"""
        return (
            f"Signal(symbol='{self.symbol}', action={self.action}, "
            f"confidence={self.confidence_score.value}, "
            f"strength={self.strength})"
        )
