from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from domain.value_objects import (
    ConfidenceScore,
    Currency,
    Price,
    Signal,
    SignalAction,
    SignalStrength,
)


def test_signal_action_properties():
    assert SignalAction.BUY.label_en == "Buy"
    assert SignalAction.SELL.color == "red"


def test_confidence_score_validation_and_properties():
    cs = ConfidenceScore(Decimal("0.756"))
    # Rounded to 2 decimals
    assert cs.value == Decimal("0.76")
    assert cs.percentage == Decimal("76")
    assert cs.strength == SignalStrength.STRONG
    assert cs.is_high() is True
    assert cs.is_reliable() is True

    # From percentage
    cs2 = ConfidenceScore.from_percentage(50)
    assert cs2.value == Decimal("0.50")
    assert cs2.strength == SignalStrength.MODERATE

    with pytest.raises(ValueError):
        ConfidenceScore(Decimal("-0.1"))
    with pytest.raises(ValueError):
        ConfidenceScore(Decimal("1.1"))


def test_signal_composite_and_validity_and_actionable():
    now = datetime.now()
    cs = ConfidenceScore(Decimal("0.5"))
    # Without sub-scores, composite is confidence
    sig = Signal(
        symbol="SYM",
        action=SignalAction.HOLD,
        confidence_score=cs,
        generated_at=now,
    )
    assert sig.composite_score == cs.value
    assert sig.is_valid() is True
    assert sig.is_actionable() is False

    # With expiration in past
    past = now - timedelta(days=1)
    sig2 = None
    try:
        sig2 = Signal(
            symbol="SYM",
            action=SignalAction.BUY,
            confidence_score=cs,
            generated_at=now,
            expires_at=past,
        )
    except ValueError:
        assert sig2 is None
    else:
        assert sig2.is_valid() is False
        assert sig2.is_actionable() is False

    # With sub-scores
    sig3 = Signal(
        symbol="SYM",
        action=SignalAction.SELL,
        confidence_score=cs,
        generated_at=now,
        technical_score=Decimal("0.8"),
        fundamental_score=Decimal("0.6"),
        market_context_score=Decimal("0.4"),
    )
    assert sig3.composite_score == Decimal("0.64")


def test_signal_price_target_stop_loss_validation():
    now = datetime.now()
    pt = Price(Decimal("10"), Currency.USD)
    sl = Price(Decimal("9"), Currency.USD)
    # SELL must have stop_loss > price_target
    with pytest.raises(ValueError):
        Signal(
            symbol="SYM",
            action=SignalAction.SELL,
            confidence_score=ConfidenceScore(Decimal("0.6")),
            generated_at=now,
            price_target=pt,
            stop_loss=sl,
        )
    # BUY must have price_target > stop_loss
    with pytest.raises(ValueError):
        Signal(
            symbol="SYM",
            action=SignalAction.BUY,
            confidence_score=ConfidenceScore(Decimal("0.6")),
            generated_at=now,
            price_target=sl,
            stop_loss=pt,
        )
