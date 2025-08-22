from datetime import datetime, timedelta
from decimal import Decimal

import pytest

from src.domain.value_objects import (
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


def test_signal_to_dict_and_from_dict():
    now = datetime.now()
    cs = ConfidenceScore(Decimal("0.8"))
    pt = Price(Decimal("10"), Currency.USD)
    sig = Signal(
        symbol="SYM",
        action=SignalAction.BUY,
        confidence_score=cs,
        generated_at=now,
        price_target=pt,
        reasoning="Test",
        indicators_used=["RSI"],
        metadata={"foo": "bar"},
    )
    d = sig.to_dict()
    sig2 = Signal.from_dict(d)
    assert sig2.symbol == "SYM"
    assert sig2.action == SignalAction.BUY
    assert sig2.confidence_score.value == cs.value
    assert sig2.price_target.value == pt.value
    assert sig2.reasoning == "Test"
    assert sig2.indicators_used == ["RSI"]
    assert sig2.metadata["foo"] == "bar"


def test_signal_add_metadata():
    now = datetime.now()
    cs = ConfidenceScore(Decimal("0.8"))
    sig = Signal(
        symbol="SYM",
        action=SignalAction.BUY,
        confidence_score=cs,
        generated_at=now,
    )
    sig2 = sig.add_metadata("bar", 42)
    assert sig2.metadata["bar"] == 42
    assert sig.metadata.get("bar") is None


def test_signal_get_potential_return_percentage():
    now = datetime.now()
    cs = ConfidenceScore(Decimal("0.8"))
    pt = Price(Decimal("12"), Currency.USD)
    sig = Signal(
        symbol="SYM",
        action=SignalAction.BUY,
        confidence_score=cs,
        generated_at=now,
        price_target=pt,
    )
    current_price = Price(Decimal("10"), Currency.USD)
    pct = sig.get_potential_return_percentage(current_price)
    assert pct == Decimal("20")
    # SELL
    sig_sell = Signal(
        symbol="SYM",
        action=SignalAction.SELL,
        confidence_score=cs,
        generated_at=now,
        price_target=Price(Decimal("8"), Currency.USD),
    )
    pct2 = sig_sell.get_potential_return_percentage(current_price)
    assert pct2 == Decimal("20")
    # HOLD
    sig_hold = Signal(
        symbol="SYM",
        action=SignalAction.HOLD,
        confidence_score=cs,
        generated_at=now,
    )
    assert sig_hold.get_potential_return_percentage(current_price) is None


def test_signal_calculate_risk_reward_ratio():
    now = datetime.now()
    cs = ConfidenceScore(Decimal("0.8"))
    sig = Signal(
        symbol="SYM",
        action=SignalAction.BUY,
        confidence_score=cs,
        generated_at=now,
        price_target=Price(Decimal("12"), Currency.USD),
        stop_loss=Price(Decimal("9"), Currency.USD),
    )
    current_price = Price(Decimal("10"), Currency.USD)
    rr = sig.calculate_risk_reward_ratio(current_price)
    assert rr == Decimal("2")
    # SELL
    sig_sell = Signal(
        symbol="SYM",
        action=SignalAction.SELL,
        confidence_score=cs,
        generated_at=now,
        price_target=Price(Decimal("8"), Currency.USD),
        stop_loss=Price(Decimal("11"), Currency.USD),
    )
    rr2 = sig_sell.calculate_risk_reward_ratio(current_price)
    assert rr2 == Decimal("2")
    # HOLD
    sig_hold = Signal(
        symbol="SYM",
        action=SignalAction.HOLD,
        confidence_score=cs,
        generated_at=now,
    )
    assert sig_hold.calculate_risk_reward_ratio(current_price) is None


def test_confidence_score_format_and_str():
    cs = ConfidenceScore(Decimal("0.75"))
    assert cs.format() == "75%"
    assert str(cs) == "75%"


def test_confidence_score_invalid_type():
    # Test passage d'un float ou str
    cs = ConfidenceScore(0.5)
    assert cs.value == Decimal("0.50")
    cs2 = ConfidenceScore("0.7")
    assert cs2.value == Decimal("0.70")


def test_signal_validation_errors():
    now = datetime.now()
    cs = ConfidenceScore(Decimal("0.8"))
    pt = Price(Decimal("10"), Currency.USD)
    sl = Price(Decimal("12"), Currency.USD)
    # BUY: price_target <= stop_loss
    with pytest.raises(ValueError):
        Signal(
            symbol="SYM",
            action=SignalAction.BUY,
            confidence_score=cs,
            generated_at=now,
            price_target=pt,
            stop_loss=sl,
        )
    # SELL: stop_loss <= price_target
    with pytest.raises(ValueError):
        Signal(
            symbol="SYM",
            action=SignalAction.SELL,
            confidence_score=cs,
            generated_at=now,
            price_target=sl,
            stop_loss=pt,
        )
    # Expiry before generated_at
    with pytest.raises(ValueError):
        Signal(
            symbol="SYM",
            action=SignalAction.BUY,
            confidence_score=cs,
            generated_at=now,
            expires_at=now - timedelta(days=1),
        )
    # Symbol manquant
    with pytest.raises(ValueError):
        Signal(
            symbol="",
            action=SignalAction.BUY,
            confidence_score=cs,
            generated_at=now,
        )


def test_signal_to_dict_handles_none():
    now = datetime.now()
    cs = ConfidenceScore(Decimal("0.8"))
    sig = Signal(
        symbol="SYM",
        action=SignalAction.BUY,
        confidence_score=cs,
        generated_at=now,
    )
    d = sig.to_dict()
    assert d["price_target"] is None
    assert d["stop_loss"] is None
    assert d["reasoning"] is None
    assert d["expires_at"] is None
