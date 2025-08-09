import pytest

from infrastructure.persistence.models.market_data import MarketData


def test_market_data_example():
    # Exemple de test pour market_data
    market_data = MarketData(
        time="2025-08-08 12:00:00", symbol="AAPL", interval_type="1d"
    )
    assert market_data.symbol == "AAPL"
    assert market_data.interval_type == "1d"
