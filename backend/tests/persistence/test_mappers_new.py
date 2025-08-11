from unittest.mock import MagicMock

def test_user_mapper_update_model():
    user = MagicMock()
    user.preferred_currency.value = "USD"
    class Role:
        value = "USER"
        def __str__(self):
            return self.value
    domain = MagicMock()
    domain.email = "b@c.com"
    domain.username = "v"
    domain.first_name = "g"
    domain.last_name = "h"
    domain.role = Role()
    domain.preferred_currency.value = "EUR"
    domain.is_active = False
    domain.email_verified = False
    domain.two_factor_enabled = True
    domain.last_login = None
    mappers_new.UserMapper.update_model(user, domain)
    assert user.email == "b@c.com"
    assert user.role.value == "USER"

def test_portfolio_mapper_update_model():
    model = MagicMock()
    entity = MagicMock()
    entity.name = "B"
    entity.description = "desc2"
    entity.base_currency.value = "EUR"
    entity.initial_cash.amount = 200
    entity.current_cash.amount = 200
    entity.total_invested.amount = 10
    entity.total_value.amount = 210
    entity.updated_at = 123
    mappers_new.PortfolioMapper.update_model(model, entity)
    assert model.name == "B"
    assert model.base_currency == "EUR"

def test_market_data_mapper_to_domain_and_to_model():
    from decimal import Decimal
    from datetime import datetime
    from src.infrastructure.persistence.models.market_data import MarketData
    from unittest.mock import MagicMock
    model = MagicMock(spec=MarketData)
    model.symbol = "AAPL"
    model.time = datetime(2024, 1, 1, 12, 0, 0)
    model.open_price = Decimal("1")
    model.high_price = Decimal("2")
    model.low_price = Decimal("1")
    model.close_price = Decimal("1.5")
    model.volume = 100
    model.interval_type = "1d"
    model.source = "yahoo_finance"
    domain = mappers_new.MarketDataMapper.to_domain(model)
    assert domain.symbol == "AAPL"
    entity = MagicMock()
    entity.timestamp = 123
    entity.symbol = "AAPL"
    entity.interval_type = "1d"
    entity.open_price.amount = 1
    entity.high_price.amount = 2
    entity.low_price.amount = 0
    entity.close_price.amount = 1.5
    entity.volume = 100
    entity.source = "yahoo"
    model2 = mappers_new.MarketDataMapper.to_model(entity)
    assert model2.symbol == "AAPL"

def test_investment_mapper_to_domain_to_persistence_and_update():
    instrument = MagicMock()
    instrument.symbol = "AAPL"
    instrument.name = "Apple"
    instrument.instrument_type = "stock"
    instrument.exchange = "NASDAQ"
    instrument.currency = "USD"
    instrument.sector = "tech"
    instrument.industry = "hardware"
    domain = mappers_new.InvestmentMapper.to_domain(instrument)
    assert domain.symbol == "AAPL"
    entity = MagicMock()
    entity.symbol = "AAPL"
    entity.name = "Apple"
    entity.exchange = "NASDAQ"
    entity.sector.value = "tech"
    entity.industry = "hardware"
    entity.market_cap = 1000
    entity.description = "desc"
    persistence = mappers_new.InvestmentMapper.to_persistence(entity)
    assert persistence.symbol == "AAPL"
    model = MagicMock()
    mappers_new.InvestmentMapper.update_instrument_model(model, entity)
    assert model.symbol == "AAPL"
    assert model.is_active is True
import src.infrastructure.persistence.mappers_new as mappers_new

def test_user_mapper_to_domain_and_to_persistence():
    class DummyUser:
        id = 1
        email = "test@example.com"
        username = "testuser"
        first_name = "Test"
        last_name = "User"
        role = "ADMIN"
        is_active = True
        is_verified = True
        created_at = None
        last_login_at = None
    
    domain_user = mappers_new.UserMapper.to_domain(DummyUser())
    assert domain_user.email == "test@example.com"
    assert domain_user.username == "testuser"
    assert domain_user.role.value == "admin"
    
    # Minimal domain user for to_persistence
    class DomainUser:
        id = 1
        email = "test@example.com"
        username = "testuser"
        first_name = "Test"
        last_name = "User"
        role = type("Role", (), {"value": "ADMIN"})()
        is_active = True
        email_verified = True
        created_at = None
        last_login = None
    
    persistence_user = mappers_new.UserMapper.to_persistence(DomainUser())
    assert persistence_user.email == "test@example.com"
    assert persistence_user.username == "testuser"
    assert persistence_user.role == "ADMIN"

def test_portfolio_mapper_to_domain_and_to_model():
    class DummyPortfolio:
        id = 1
        user_id = 2
        name = "Test Portfolio"
        description = "desc"
        base_currency = "USD"
        initial_cash = 1000
        current_cash = 1000
        total_invested = 0
        total_value = 1000
        created_at = None
        updated_at = None
    
    # Adapter le DummyPortfolio pour ne pas passer 'description' à Portfolio.create()
    class DummyPortfolioNoDesc:
        id = 1
        user_id = 2
        name = "Test Portfolio"
        description = None
        base_currency = "USD"
        initial_cash = 1000
        current_cash = 1000
        total_invested = 0
        total_value = 1000
        created_at = None
        updated_at = None
    domain_portfolio = mappers_new.PortfolioMapper.to_domain(DummyPortfolioNoDesc())
    assert domain_portfolio.name == "Test Portfolio"
    assert domain_portfolio.base_currency.value == "USD"

    class DomainPortfolio:
        id = 1
        user_id = 2
        name = "Test Portfolio"
        description = "desc"
        base_currency = type("Currency", (), {"value": "USD"})()
        initial_cash = type("Money", (), {"amount": 1000, "currency": type("Currency", (), {"value": "USD"})()})()
        current_cash = type("Money", (), {"amount": 1000, "currency": type("Currency", (), {"value": "USD"})()})()
        total_invested = type("Money", (), {"amount": 0})()
        total_value = type("Money", (), {"amount": 1000})()
        created_at = None
        updated_at = None
    
    model_portfolio = mappers_new.PortfolioMapper.to_model(DomainPortfolio())
    assert model_portfolio.name == "Test Portfolio"
    assert model_portfolio.base_currency == "USD"
