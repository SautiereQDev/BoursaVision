import pytest

from infrastructure.persistence.models.fundamental import FundamentalData


def test_fundamental_example():
    # Exemple de test pour fundamental
    fundamental = FundamentalData(
        instrument_id="00000000-0000-0000-0000-000000000000",
        symbol="AAPL",
        period_end_date="2025-08-08",
        period_type="annual",
    )
    assert fundamental.symbol == "AAPL"
    assert fundamental.period_type == "annual"
