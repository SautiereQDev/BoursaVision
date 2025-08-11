import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
from src.infrastructure.persistence.repositories import (
    SQLAlchemyUserRepository,
    SQLAlchemyPortfolioRepository,
    SQLAlchemyMarketDataRepository,
    SQLAlchemyInvestmentRepository,
)

# Sous-classes de test pour contourner l'abstraction

# User repo: injects session and _mapper
from src.infrastructure.persistence.mappers_new import UserMapper, PortfolioMapper, InvestmentMapper
from src.infrastructure.persistence.mappers import MarketDataMapper
class TestUserRepo(SQLAlchemyUserRepository):
    __test__ = False
    def __init__(self, session):
        self._session = session
        self._mapper = UserMapper()

class TestPortfolioRepo(SQLAlchemyPortfolioRepository):
    __test__ = False
    def __init__(self):
        self._mapper = PortfolioMapper()
    # override methods to avoid abstract errors
    async def find_by_name(self, name): return None
    async def exists(self, portfolio_id): return False
    async def find_all(self): return []
    async def find_by_ids(self, ids): return []
    async def find_by_user_ids(self, user_ids): return []
    async def count_by_user(self, user_id): return 0
    async def exists_by_name(self, name): return False

class TestMarketDataMapper:
    def to_persistence(self, market_data):
        return {
            "time": market_data.timestamp,
            "symbol": market_data.symbol,
            "interval_type": getattr(market_data, "interval_type", "1d"),
            "open_price": market_data.open_price,
            "high_price": market_data.high_price,
            "low_price": market_data.low_price,
            "close_price": market_data.close_price,
            "adjusted_close": market_data.adjusted_close or market_data.close_price,
            "volume": market_data.volume,
            "source": str(market_data.source),
            "created_at": market_data.created_at,
        }
    def to_domain(self, model):
        return model  # Not needed for this minimal test

class TestMarketDataRepo(SQLAlchemyMarketDataRepository):
    __test__ = False
    def __init__(self):
        self._mapper = TestMarketDataMapper()
    # override methods to avoid abstract errors
    async def find_by_id(self, id): return None
    async def delete(self, id): return False
    async def find_all(self): return []
    async def find_by_ids(self, ids): return []
    async def exists(self, id): return False
    async def find_by_symbol(self, symbol): return None
    async def find_latest(self): return None
    async def find_by_timerange(self, start, end): return []
    async def find_by_symbols_and_timerange(self, symbols, start, end): return []
    async def find_by_symbol_and_interval(self, symbol, interval): return []
    async def find_by_symbol_and_time(self, symbol, time): return None
    async def cleanup_old_data(self): return 0
    async def count_by_symbol(self, symbol): return 0
    async def delete_by_symbol_and_date_range(self, symbol, start, end): return 0
    async def exists_by_symbol_and_timestamp(self, symbol, timestamp): return False
    async def find_by_symbol_and_timestamp(self, symbol, timestamp): return None
    async def find_latest_by_symbols(self, symbols): return []
    async def find_missing_dates(self, symbol): return []
    async def get_available_symbols(self): return []
    async def get_date_range_for_symbol(self, symbol): return (None, None)

class TestInvestmentRepo(SQLAlchemyInvestmentRepository):
    __test__ = False
    def __init__(self, session):
        self._session = session
        self._mapper = InvestmentMapper()
    async def find_all_active(self): return []
from src.domain.entities.user import User as DomainUser
from src.domain.entities.portfolio import Portfolio as DomainPortfolio
from src.domain.entities.market_data import MarketData as DomainMarketData, MarketDataArgs, Timeframe, DataSource
from src.domain.value_objects.price import Price
from src.domain.value_objects.money import Currency
from src.domain.entities.investment import Investment

@pytest.mark.asyncio
async def test_user_repository_find_by_id():
    session = AsyncMock()
    repo = TestUserRepo(session)
    user_id = uuid4()
    user_mock = MagicMock()
    user_mock.id = user_id
    user_mock.email = "test@example.com"
    user_mock.username = "testuser"
    user_mock.first_name = "Test"
    user_mock.last_name = "User"
    user_mock.role = "ADMIN"
    user_mock.is_active = True
    user_mock.is_verified = True
    user_mock.created_at = None
    user_mock.last_login_at = None
    # Fix async mock: session.execute returns an AsyncMock whose scalar_one_or_none returns user_mock
    execute_result = AsyncMock()
    execute_result.scalar_one_or_none = lambda: user_mock
    session.execute.return_value = execute_result
    result = await repo.find_by_id(user_id)
    assert result is not None

@pytest.mark.asyncio
@patch("src.infrastructure.persistence.repositories.portfolio_repository.get_db_session")
async def test_portfolio_repository_find_by_id(mock_get_db_session):
    session = AsyncMock()
    repo = TestPortfolioRepo()
    portfolio_id = uuid4()
    portfolio_mock = MagicMock()
    portfolio_mock.id = portfolio_id
    portfolio_mock.user_id = uuid4()
    portfolio_mock.name = "Test Portfolio"
    portfolio_mock.base_currency = "USD"
    portfolio_mock.initial_cash = 1000
    portfolio_mock.current_cash = 1000
    portfolio_mock.total_invested = 0
    portfolio_mock.total_value = 1000
    portfolio_mock.created_at = None
    portfolio_mock.updated_at = None
    portfolio_mock.positions = []
    execute_result = AsyncMock()
    execute_result.scalar_one_or_none = lambda: portfolio_mock
    session.execute.return_value = execute_result
    class DummyAsyncContext:
        async def __aenter__(self): return session
        async def __aexit__(self, exc_type, exc, tb): return None
    mock_get_db_session.return_value = DummyAsyncContext()
    result = await repo.find_by_id(portfolio_id)
    assert result is not None

@pytest.mark.asyncio
@patch("src.infrastructure.persistence.repositories.market_data_repository.get_db_session")
async def test_market_data_repository_save(mock_get_db_session):
    session = AsyncMock()
    repo = TestMarketDataRepo()
    from datetime import datetime
    from decimal import Decimal
    args = MarketDataArgs(
        symbol="AAPL",
        timestamp=datetime(2023, 1, 1, 10, 0, 0),
        open_price=Decimal("100"),
        high_price=Decimal("110"),
        low_price=Decimal("90"),
        close_price=Decimal("105"),
        volume=1000,
        timeframe=Timeframe.DAY_1,
        source=DataSource.INTERNAL,
        currency=Currency.USD,
        adjusted_close=Decimal("105")
    )
    market_data = DomainMarketData.create(args)
    execute_result = AsyncMock()
    execute_result.scalar_one_or_none = lambda: None
    session.execute.return_value = execute_result
    session.flush.return_value = None
    # Patch session.add to avoid RuntimeWarning (not awaited)
    session.add = lambda *a, **kw: None
    class DummyAsyncContext:
        async def __aenter__(self): return session
        async def __aexit__(self, exc_type, exc, tb): return None
    mock_get_db_session.return_value = DummyAsyncContext()
    result = await repo.save(market_data)
    assert result is not None

@pytest.mark.asyncio
async def test_investment_repository_find_by_symbol():
    session = AsyncMock()
    repo = TestInvestmentRepo(session)
    symbol = "AAPL"
    mock_model = MagicMock()
    mock_model.symbol = symbol
    mock_model.name = "Apple"
    mock_model.instrument_type = "stock"
    mock_model.exchange = "NASDAQ"
    mock_model.currency = "USD"
    mock_model.sector = "Tech"
    mock_model.industry = "Software"
    mock_model.is_active = True
    mock_model.fundamental_data = []
    execute_result = AsyncMock()
    execute_result.scalar_one_or_none = lambda: mock_model
    session.execute.return_value = execute_result
    result = await repo.find_by_symbol(symbol)
    assert result is not None
