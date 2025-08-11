from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest

from src.domain.entities.market_data import Currency, DataSource, MarketData, Timeframe


def test_market_data_example():
    market_data = MarketData(
        id=uuid4(),
        symbol="AAPL",
        timestamp=datetime.now(timezone.utc),
        timeframe=Timeframe.DAY_1,
        source=DataSource.YAHOO_FINANCE,
        currency=Currency.USD,
        open_price=Decimal("150.00"),
        high_price=Decimal("157.00"),
        low_price=Decimal("149.00"),
        close_price=Decimal("155.00"),
        volume=1000,
    )
    assert market_data.symbol == "AAPL"
    assert market_data.timeframe == Timeframe.DAY_1


def test_update_prices():
    market_data = MarketData(
        id=uuid4(),
        symbol="AAPL",
        timestamp=datetime.now(timezone.utc),
        timeframe=Timeframe.DAY_1,
        source=DataSource.YAHOO_FINANCE,
        currency=Currency.USD,
        open_price=Decimal("150.00"),
        high_price=Decimal("157.00"),
        low_price=Decimal("149.00"),
        close_price=Decimal("155.00"),
        volume=1000,
    )
    market_data.update_prices(
        open_price=Decimal("160.00"),
        close_price=Decimal("165.00"),
        high_price=Decimal("167.00"),
        low_price=Decimal("159.00"),
        volume=1200,
    )
    assert market_data.open_price == Decimal("160.00")
    assert market_data.close_price == Decimal("165.00")


def test_get_typical_price():
    market_data = MarketData(
        id=uuid4(),
        symbol="AAPL",
        timestamp=datetime.now(timezone.utc),
        timeframe=Timeframe.DAY_1,
        source=DataSource.YAHOO_FINANCE,
        currency=Currency.USD,
        open_price=Decimal("150.00"),
        high_price=Decimal("157.00"),
        low_price=Decimal("149.00"),
        close_price=Decimal("155.00"),
        volume=1000,
    )
    typical_price = market_data.get_typical_price()
    assert round(typical_price, 2) == Decimal("153.67")  # (High + Low + Close) / 3


def test_is_gap_up():
    market_data = MarketData(
        id=uuid4(),
        symbol="AAPL",
        timestamp=datetime.now(timezone.utc),
        timeframe=Timeframe.DAY_1,
        source=DataSource.YAHOO_FINANCE,
        currency=Currency.USD,
        open_price=Decimal("150.00"),
        high_price=Decimal("157.00"),
        low_price=Decimal("149.00"),
        close_price=Decimal("155.00"),
        volume=1000,
    )
    market_data.adjusted_close = Decimal(
        "148.00"
    )  # Ajout de la valeur pour adjusted_close
    assert market_data.is_gap_up(threshold_percent=Decimal("1.5")) is False
    market_data.update_prices(
        open_price=Decimal("160.00"),
        close_price=Decimal("165.00"),
        high_price=Decimal("167.00"),
        low_price=Decimal("159.00"),
        volume=1200,
    )
    market_data.adjusted_close = Decimal("150.00")  # Mise à jour de adjusted_close
    assert market_data.is_gap_up(threshold_percent=Decimal("1.5")) is True
