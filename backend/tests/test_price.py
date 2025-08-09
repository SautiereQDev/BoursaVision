from datetime import datetime
from decimal import Decimal

import pytest

from domain.value_objects.money import Currency, Money
from domain.value_objects.price import Price, PriceData, PricePoint


def test_price_creation_and_rounding():
    p = Price(Decimal("1.23456"), Currency.USD, datetime(2021, 1, 1))
    assert p.value == Decimal("1.2346")
    with pytest.raises(ValueError):
        Price(Decimal("-1"), Currency.EUR)
    with pytest.raises(ValueError):
        Price(Decimal("1000000"), Currency.GBP)


def test_price_to_money_and_comparisons_and_format():
    p = Price(Decimal("2.00"), Currency.USD)
    money = p.to_money(Decimal("3"))
    assert isinstance(money, Money)
    assert money == Money(Decimal("6.00"), Currency.USD)
    p1 = Price(Decimal("5"), Currency.EUR)
    p2 = Price(Decimal("3"), Currency.EUR)
    assert p1.is_higher_than(p2)
    assert not p2.is_higher_than(p1)
    with pytest.raises(ValueError):
        p1.change_from(Price(Decimal("1"), Currency.USD))
    assert p1.format() == "5 EUR"
    assert p1.format(include_currency=False) == "5"


def test_price_change_and_percentage():
    p_prev = Price(Decimal("10"), Currency.USD)
    p_curr = Price(Decimal("15"), Currency.USD)
    assert p_curr.change_from(p_prev) == Decimal("5")
    assert p_curr.change_percentage_from(p_prev) == Decimal("50")
    p_zero = Price(Decimal("0"), Currency.USD)
    assert p_curr.change_percentage_from(p_zero) == Decimal("0")


def test_pricepoint_and_pricedata_validations_and_properties():
    t = datetime(2021, 1, 1)
    p_open = Price(Decimal("1"), Currency.USD, t)
    p_high = Price(Decimal("2"), Currency.USD, t)
    p_low = Price(Decimal("0.5"), Currency.USD, t)
    p_close = Price(Decimal("1.5"), Currency.USD, t)
    pp = PricePoint(t, p_open, p_high, p_low, p_close, volume=100)
    assert pp.currency == Currency.USD
    assert pp.price_range == Decimal("1.5")
    assert pp.price_change == Decimal("0.5")
    assert isinstance(pp.is_bullish(), bool)
    assert isinstance(pp.is_doji(), bool)
    # PriceData
    pd = PriceData("SYM", [pp], "1d")
    assert pd.symbol == "SYM"
    assert pd.latest_price == p_close
    assert pd.oldest_price == p_close
    assert pd.period_return == Decimal("0")
    assert pd.highest_price == p_high
    assert pd.total_volume == 100
    assert list(pd) == [pp]
    assert pd[0] == pp
    # invalid PriceData
    with pytest.raises(ValueError):
        PriceData("", [], "1d")
