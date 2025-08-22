from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from src.domain.entities import (
    InsufficientFundsException,
    Portfolio,
    PositionLimitExceededException,
)
from src.domain.events import InvestmentAddedEvent, PortfolioCreatedEvent
from src.domain.value_objects import Currency, Money


def test_portfolio_create_and_event():
    user_id = uuid4()
    name = "MyPortfolio"
    currency = Currency.USD
    initial_cash = Money(Decimal("100.00"), currency)
    portfolio = Portfolio.create(user_id, name, currency, initial_cash)

    # Check attributes
    assert isinstance(portfolio.id, UUID)
    assert portfolio.user_id == user_id
    assert portfolio.name == name
    assert portfolio.base_currency == currency
    assert portfolio.cash_balance == initial_cash
    assert isinstance(portfolio.created_at, datetime)

    # Domain events
    events = portfolio.get_domain_events()
    assert len(events) == 1
    evt = events[0]
    assert isinstance(evt, PortfolioCreatedEvent)
    assert evt.user_id == user_id
    assert evt.name == name
    assert isinstance(evt.timestamp, datetime)


def test_add_investment_success_and_total_value():
    user_id = uuid4()
    initial_cash = Money(Decimal("100.00"), Currency.USD)
    portfolio = Portfolio.create(user_id, "P", "USD", initial_cash)

    # Add investment
    symbol = "SYM"
    price = Money(Decimal("10.00"), Currency.USD)
    qty = 1
    tx_date = datetime.now(timezone.utc)
    portfolio.clear_domain_events()
    portfolio.add_investment(symbol, qty, price, tx_date)

    # Cash decreased
    assert portfolio.cash_balance == Money(Decimal("90.00"), Currency.USD)
    # Position added
    positions = portfolio.positions
    assert symbol in positions
    pos = positions[symbol]
    assert pos.quantity == qty
    assert pos.average_price == price

    # Total value calculation
    current_prices = {symbol: Money(Decimal("12.00"), Currency.USD)}
    total_value = portfolio.calculate_total_value(current_prices)
    expected_value = Money(Decimal("90.00"), Currency.USD) + Money(
        Decimal("12.00"), Currency.USD
    )
    assert total_value == expected_value

    # Domain event for investment
    events = portfolio.get_domain_events()
    assert len(events) == 1
    inv_evt = events[0]
    assert isinstance(inv_evt, InvestmentAddedEvent)
    assert inv_evt.symbol == symbol
    assert inv_evt.quantity == qty
    assert inv_evt.price == price


@pytest.mark.parametrize(
    "cash, price, qty",
    [
        (Money(Decimal("10"), Currency.USD), Money(Decimal("5"), Currency.USD), 3),
        (Money(Decimal("100"), Currency.USD), Money(Decimal("20"), Currency.USD), 1),
    ],
)
def test_add_investment_insufficient_or_limit_exceeded(cash, price, qty):
    # First case: insufficient funds; second: limit exceeded
    user_id = uuid4()
    portfolio = Portfolio.create(user_id, "P", "USD", cash)
    portfolio.clear_domain_events()
    with pytest.raises((InsufficientFundsException, PositionLimitExceededException)):
        portfolio.add_investment("SYM", qty, price, datetime.now(timezone.utc))
