import pytest

from src.infrastructure.persistence.models.instruments import Instrument


def test_instruments_example():
    # Exemple de test pour instruments
    instrument = Instrument(symbol="AAPL", name="Apple Inc.", instrument_type="stock")
    assert instrument.symbol == "AAPL"
    assert instrument.name == "Apple Inc."
    assert instrument.instrument_type == "stock"
