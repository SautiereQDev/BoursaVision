from decimal import Decimal

import pytest

from domain.value_objects.money import Currency, Money


def test_currency_properties():
    assert Currency.USD.symbol == "$"
    assert Currency.EUR.decimal_places == 2
    assert Currency.JPY.decimal_places == 0
    assert Currency.GBP.names == "British Pound"


def test_money_creation_and_rounding():
    m = Money(Decimal("1.234"), Currency.USD)
    assert m.amount == Decimal("1.23")
    m_jpy = Money(Decimal("100.6"), Currency.JPY)
    assert m_jpy.amount == Decimal("101")


def test_money_addition_same_currency():
    m1 = Money(Decimal("10"), Currency.EUR)
    m2 = Money(Decimal("5"), Currency.EUR)
    result = m1 + m2
    assert result == Money(Decimal("15"), Currency.EUR)


def test_money_addition_diff_currency_raises():
    m_usd = Money(Decimal("1"), Currency.USD)
    m_eur = Money(Decimal("1"), Currency.EUR)
    with pytest.raises(ValueError):
        _ = m_usd + m_eur


def test_money_subtraction():
    m1 = Money(Decimal("10"), Currency.GBP)
    m2 = Money(Decimal("4"), Currency.GBP)
    assert m1 - m2 == Money(Decimal("6"), Currency.GBP)


def test_money_subtraction_negative_result_raises():
    m1 = Money(Decimal("2"), Currency.CAD)
    m2 = Money(Decimal("5"), Currency.CAD)
    with pytest.raises(ValueError):
        _ = m1 - m2


def test_money_multiplication_division():
    m = Money(Decimal("2.50"), Currency.USD)
    assert m * Decimal("2") == Money(Decimal("5.00"), Currency.USD)
    assert m / Decimal("2") == Money(Decimal("1.25"), Currency.USD)
    with pytest.raises(ZeroDivisionError):
        _ = m / Decimal("0")


def test_money_comparisons():
    m1 = Money(Decimal("5"), Currency.USD)
    m2 = Money(Decimal("10"), Currency.USD)
    assert m1 < m2
    assert m1 <= m2
    assert m2 > m1
    assert m2 >= m1
    with pytest.raises(ValueError):
        _ = m1 < Money(Decimal("1"), Currency.EUR)


def test_money_convert_to():
    m = Money(Decimal("10"), Currency.USD)
    converted = m.convert_to(Currency.EUR, Decimal("0.9"))
    assert converted == Money(Decimal("9.00"), Currency.EUR)
    same = m.convert_to(Currency.USD, Decimal("1"))
    assert same == m
    with pytest.raises(ValueError):
        _ = m.convert_to(Currency.EUR, Decimal("0"))


def test_money_zero_and_is_zero():
    m = Money.zero(Currency.USD)
    assert m.amount == 0
    assert m.is_zero()
    m2 = Money(Decimal("1"), Currency.USD)
    assert not m2.is_zero()


def test_money_from_float_and_from_string():
    m = Money.from_float(1.23, Currency.EUR)
    assert m.amount == Decimal("1.23")
    m2 = Money.from_string("1,234.56", Currency.USD)
    assert m2.amount == Decimal("1234.56")
    with pytest.raises(ValueError):
        Money.from_string("-42", Currency.GBP)
