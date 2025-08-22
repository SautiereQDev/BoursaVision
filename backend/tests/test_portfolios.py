import pytest

from src.infrastructure.persistence.models.portfolios import Portfolio


def test_portfolios_example():
    # Exemple de test pour portfolios
    portfolio = Portfolio(
        user_id="00000000-0000-0000-0000-000000000000",
        name="My Portfolio",
        base_currency="USD",
    )
    assert portfolio.name == "My Portfolio"
    assert portfolio.base_currency == "USD"
