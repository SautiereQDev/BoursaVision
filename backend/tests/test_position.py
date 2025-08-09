from datetime import datetime, timezone
from decimal import Decimal

import pytest

from domain.entities.portfolio import Position
from domain.value_objects.money import Currency, Money


def test_calculate_market_value():
    dt = datetime(2021, 1, 1, tzinfo=timezone.utc)
    pos = Position("SYM", 10, Money(Decimal("2.50"), Currency.USD), dt, dt)
    mv = pos.calculate_market_value(Money(Decimal("3.00"), Currency.USD))
    assert mv == Money(Decimal("30.00"), Currency.USD)


def test_calculate_unrealized_pnl():
    dt = datetime(2021, 1, 1, tzinfo=timezone.utc)
    avg_price = Money(Decimal("2.00"), Currency.USD)
    pos = Position("SYM", 5, avg_price, dt, dt)
    pnl = pos.calculate_unrealized_pnl(Money(Decimal("3.00"), Currency.USD))
    assert pnl == Money(Decimal("5.00"), Currency.USD)


def test_calculate_return_percentage():
    dt = datetime(2021, 1, 1, tzinfo=timezone.utc)
    avg_price = Money(Decimal("2.00"), Currency.USD)
    pos = Position("SYM", 1, avg_price, dt, dt)
    ret_pct = pos.calculate_return_percentage(Money(Decimal("3.00"), Currency.USD))
    assert ret_pct == pytest.approx(50.0)
    pos_zero = Position("SYM", 1, Money(Decimal("0"), Currency.USD), dt, dt)
    assert pos_zero.calculate_return_percentage(
        Money(Decimal("3.00"), Currency.USD)
    ) == pytest.approx(0.0)
