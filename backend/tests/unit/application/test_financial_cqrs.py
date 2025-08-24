"""
Unit Tests for Financial CQRS Implementation
============================================

Comprehensive tests for commands, queries, handlers, and services
leveraging the complete financial schema.
"""
import pytest
from decimal import Decimal
from datetime import datetime, UTC
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock

from boursa_vision.application.commands.portfolio.create_portfolio_command import (
    CreatePortfolioCommand,
)
from boursa_vision.application.commands.portfolio.add_investment_to_portfolio_command import (
    AddInvestmentToPortfolioCommand,
)
from boursa_vision.application.queries.portfolio.financial_queries import (
    GetPortfolioPerformanceQuery,
    GetPortfolioSummaryQuery,
    GetPortfolioValuationQuery,
)
from boursa_vision.application.handlers.financial_query_handlers import (
    GetPortfolioPerformanceQueryHandler,
    GetPortfolioSummaryQueryHandler,
    GetPortfolioValuationQueryHandler,
)
from boursa_vision.domain.entities.portfolio import Portfolio, Position
from boursa_vision.domain.entities.market_data import MarketData
from boursa_vision.domain.services.portfolio_valuation_service import PortfolioValuationService
from boursa_vision.domain.services.performance_analysis_service import PerformanceAnalysisService
from boursa_vision.domain.value_objects import Money, Currency


class TestCreatePortfolioCommand:
    """Test cases for CreatePortfolioCommand with complete financial schema"""

    def test_create_portfolio_command_validation(self):
        """Test command validation with complete financial fields"""
        user_id = uuid4()
        command = CreatePortfolioCommand(
            user_id=user_id,
            name="Test Portfolio",
            description="A test portfolio for investment tracking",
            initial_cash_amount=Decimal("10000.00"),
            base_currency="USD",
            is_default=False,
        )

        assert command.user_id is not None
        assert command.name == "Test Portfolio"
        assert command.base_currency == "USD"
        assert command.initial_cash_amount == Decimal("10000.00")
        assert command.description == "A test portfolio for investment tracking"

    def test_create_portfolio_command_defaults(self):
        """Test command with default values"""
        command = CreatePortfolioCommand(
            user_id=uuid4(),
            name="Default Portfolio",
        )

        assert command.base_currency == "USD"
        assert command.initial_cash_amount == Decimal("0.0")
        assert command.description is None

    def test_create_portfolio_command_validation_errors(self):
        """Test command validation with invalid data"""
        # Test empty name
        with pytest.raises(ValueError, match="Portfolio name cannot be empty"):
            CreatePortfolioCommand(
                user_id=uuid4(),
                name="",
            )

        # Test negative initial cash
        with pytest.raises(ValueError, match="Initial cash amount cannot be negative"):
            CreatePortfolioCommand(
                user_id=uuid4(),
                name="Test Portfolio",
                initial_cash_amount=Decimal("-100.00"),
            )


class TestAddInvestmentToPortfolioCommand:
    """Test cases for AddInvestmentToPortfolioCommand with position tracking"""

    def test_add_investment_command_validation(self):
        """Test command validation with complete position tracking"""
        command = AddInvestmentToPortfolioCommand(
            portfolio_id=uuid4(),
            symbol="AAPL",
            quantity=Decimal("100"),
            purchase_price=Decimal("150.00"),
            side="long",
            notes="Initial AAPL position"
        )

        assert command.portfolio_id is not None
        assert command.symbol == "AAPL"
        assert command.quantity == Decimal("100")
        assert command.purchase_price == Decimal("150.00")
        assert command.side == "long"

    def test_add_investment_validation_errors(self):
        """Test command validation errors"""
        # Test zero quantity
        with pytest.raises(ValueError, match="Quantity must be positive"):
            AddInvestmentToPortfolioCommand(
                portfolio_id=uuid4(),
                symbol="AAPL",
                quantity=Decimal("0"),
                purchase_price=Decimal("150.00"),
            )

        # Test negative price
        with pytest.raises(ValueError, match="Purchase price must be positive"):
            AddInvestmentToPortfolioCommand(
                portfolio_id=uuid4(),
                symbol="AAPL",
                quantity=Decimal("100"),
                purchase_price=Decimal("-10.00"),
            )


class TestPortfolioValuationService:
    """Test cases for PortfolioValuationService"""

    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        portfolio_repo = AsyncMock()
        market_data_repo = AsyncMock()
        return portfolio_repo, market_data_repo

    @pytest.fixture
    def valuation_service(self, mock_repositories):
        """Create valuation service with mocked dependencies"""
        portfolio_repo, market_data_repo = mock_repositories
        return PortfolioValuationService(portfolio_repo, market_data_repo)

    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio for testing"""
        portfolio_id = uuid4()
        user_id = uuid4()
        
        portfolio = Portfolio(
            id=portfolio_id,
            user_id=user_id,
            name="Test Portfolio",
            base_currency="USD",
            cash_balance=Money(Decimal("5000.00"), Currency.USD),
            created_at=datetime.now(UTC),
        )
        
        # Add sample position
        position = Position(
            symbol="AAPL",
            quantity=100,
            average_price=Money(Decimal("150.00"), Currency.USD),
            first_purchase_date=datetime.now(UTC),
            last_update=datetime.now(UTC),
        )
        portfolio._positions["AAPL"] = position
        
        return portfolio

    @pytest.mark.asyncio
    async def test_calculate_portfolio_value(self, valuation_service, sample_portfolio, mock_repositories):
        """Test portfolio value calculation"""
        portfolio_repo, market_data_repo = mock_repositories
        
        # Mock repository responses
        portfolio_repo.find_by_id.return_value = sample_portfolio
        
        # Mock market data
        market_data = MagicMock()
        market_data.close_price = Decimal("160.00")
        market_data_repo.find_latest_by_symbol.return_value = market_data

        # Calculate portfolio value
        total_value = await valuation_service.calculate_portfolio_value(
            sample_portfolio.id,
            use_market_prices=True,
            include_cash=True,
        )

        # Verify calculation: cash (5000) + position value (100 * 160)
        expected_value = Decimal("5000.00") + (100 * Decimal("160.00"))
        assert total_value.amount == expected_value
        assert str(total_value.currency) == "USD"

    @pytest.mark.asyncio
    async def test_calculate_unrealized_pnl(self, valuation_service, sample_portfolio, mock_repositories):
        """Test unrealized P&L calculation"""
        portfolio_repo, market_data_repo = mock_repositories
        
        portfolio_repo.find_by_id.return_value = sample_portfolio
        
        # Mock market data showing price increase
        market_data = MagicMock()
        market_data.close_price = Decimal("160.00")
        market_data_repo.find_latest_by_symbol.return_value = market_data

        unrealized_pnl = await valuation_service.calculate_unrealized_pnl(sample_portfolio.id)

        # Expected: (160 - 150) * 100 = 1000
        expected_pnl = (Decimal("160.00") - Decimal("150.00")) * 100
        assert unrealized_pnl == expected_pnl


class TestFinancialQueryHandlers:
    """Test cases for financial query handlers"""

    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        portfolio_repo = AsyncMock()
        market_data_repo = AsyncMock()
        return portfolio_repo, market_data_repo

    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio for testing"""
        portfolio_id = uuid4()
        user_id = uuid4()
        
        return Portfolio(
            id=portfolio_id,
            user_id=user_id,
            name="Test Portfolio",
            base_currency="USD",
            cash_balance=Money(Decimal("5000.00"), Currency.USD),
            created_at=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_portfolio_summary_query_handler(self, mock_repositories, sample_portfolio):
        """Test GetPortfolioSummaryQueryHandler"""
        portfolio_repo, market_data_repo = mock_repositories
        
        # Setup mocks
        portfolio_repo.find_by_id.return_value = sample_portfolio
        
        # Create handler and query
        handler = GetPortfolioSummaryQueryHandler(portfolio_repo, market_data_repo)
        query = GetPortfolioSummaryQuery(
            portfolio_id=sample_portfolio.id,
            calculate_unrealized_pnl=True,
            include_position_count=True,
        )

        # Execute query
        result = await handler.handle(query)

        # Verify results
        assert result["portfolio_id"] == str(sample_portfolio.id)
        assert result["name"] == "Test Portfolio"
        assert result["base_currency"] == "USD"
        assert "current_value" in result
        assert "cash_balance" in result
        assert "positions_count" in result

    @pytest.mark.asyncio
    async def test_portfolio_valuation_query_handler(self, mock_repositories, sample_portfolio):
        """Test GetPortfolioValuationQueryHandler"""
        portfolio_repo, market_data_repo = mock_repositories
        
        # Setup mocks
        portfolio_repo.find_by_id.return_value = sample_portfolio
        
        # Create handler and query
        handler = GetPortfolioValuationQueryHandler(portfolio_repo, market_data_repo)
        query = GetPortfolioValuationQuery(
            portfolio_id=sample_portfolio.id,
            use_market_prices=True,
            include_cash=True,
            include_breakdown=True,
        )

        # Execute query
        result = await handler.handle(query)

        # Verify results
        assert result["portfolio_id"] == str(sample_portfolio.id)
        assert "total_value" in result
        assert result["use_market_prices"] is True
        assert "valuation_timestamp" in result


class TestPortfolioQueries:
    """Test cases for portfolio query objects"""

    def test_portfolio_performance_query(self):
        """Test GetPortfolioPerformanceQuery construction"""
        portfolio_id = uuid4()
        query = GetPortfolioPerformanceQuery(
            portfolio_id=portfolio_id,
            include_positions=True,
            include_historical=True,
        )

        assert query.portfolio_id == portfolio_id
        assert query.include_positions is True
        assert query.include_historical is True
        assert query.date_from is None
        assert query.date_to is None

    def test_portfolio_summary_query(self):
        """Test GetPortfolioSummaryQuery construction"""
        portfolio_id = uuid4()
        query = GetPortfolioSummaryQuery(
            portfolio_id=portfolio_id,
            calculate_unrealized_pnl=False,
            include_position_count=False,
        )

        assert query.portfolio_id == portfolio_id
        assert query.calculate_unrealized_pnl is False
        assert query.include_position_count is False

    def test_portfolio_valuation_query(self):
        """Test GetPortfolioValuationQuery construction"""
        portfolio_id = uuid4()
        query = GetPortfolioValuationQuery(
            portfolio_id=portfolio_id,
            use_market_prices=False,
            include_cash=False,
            include_breakdown=False,
        )

        assert query.portfolio_id == portfolio_id
        assert query.use_market_prices is False
        assert query.include_cash is False
        assert query.include_breakdown is False


class TestPerformanceAnalysisService:
    """Test cases for PerformanceAnalysisService"""

    @pytest.fixture
    def mock_repositories(self):
        """Create mock repositories"""
        portfolio_repo = AsyncMock()
        market_data_repo = AsyncMock()
        return portfolio_repo, market_data_repo

    @pytest.fixture
    def performance_service(self, mock_repositories):
        """Create performance service with mocked dependencies"""
        portfolio_repo, market_data_repo = mock_repositories
        return PerformanceAnalysisService(portfolio_repo, market_data_repo)

    @pytest.fixture
    def sample_portfolio(self):
        """Create sample portfolio for testing"""
        portfolio_id = uuid4()
        user_id = uuid4()
        
        return Portfolio(
            id=portfolio_id,
            user_id=user_id,
            name="Test Portfolio",
            base_currency="USD",
            cash_balance=Money(Decimal("5000.00"), Currency.USD),
            created_at=datetime.now(UTC),
        )

    @pytest.mark.asyncio
    async def test_calculate_portfolio_returns(self, performance_service, sample_portfolio, mock_repositories):
        """Test portfolio returns calculation"""
        portfolio_repo, market_data_repo = mock_repositories
        
        portfolio_repo.find_by_id.return_value = sample_portfolio

        returns = await performance_service.calculate_portfolio_returns(
            sample_portfolio.id,
            period_days=30,
            include_dividends=True,
        )

        # Verify return structure
        assert "total_return" in returns
        assert "total_return_pct" in returns
        assert "daily_return" in returns
        assert "daily_return_pct" in returns
        assert "annualized_return" in returns

    @pytest.mark.asyncio
    async def test_calculate_sharpe_ratio(self, performance_service, sample_portfolio, mock_repositories):
        """Test Sharpe ratio calculation"""
        portfolio_repo, market_data_repo = mock_repositories
        
        portfolio_repo.find_by_id.return_value = sample_portfolio

        sharpe_ratio = await performance_service.calculate_sharpe_ratio(
            sample_portfolio.id,
            risk_free_rate=Decimal("0.02"),
        )

        assert isinstance(sharpe_ratio, Decimal)
        assert sharpe_ratio >= Decimal("0.00")  # Non-negative for this mock case


# Integration Test
class TestCQRSIntegration:
    """Integration tests for complete CQRS flow"""

    @pytest.mark.asyncio
    async def test_complete_portfolio_workflow(self):
        """Test complete workflow: create portfolio -> add investment -> query performance"""
        # This would test the full CQRS flow from command to query
        # with real or comprehensive mock implementations
        
        # 1. Create portfolio command
        user_id = uuid4()
        create_command = CreatePortfolioCommand(
            user_id=user_id,
            name="Integration Test Portfolio",
            initial_cash_amount=Decimal("10000.00"),
        )
        
        # 2. Add investment command
        portfolio_id = uuid4()  # Would be returned from create
        add_investment_command = AddInvestmentToPortfolioCommand(
            portfolio_id=portfolio_id,
            symbol="AAPL",
            quantity=Decimal("100"),
            purchase_price=Decimal("150.00"),
        )
        
        # 3. Query performance
        performance_query = GetPortfolioPerformanceQuery(
            portfolio_id=portfolio_id,
            include_positions=True,
            include_historical=False,
        )
        
        # Verify command/query construction
        assert create_command.user_id == user_id
        assert add_investment_command.symbol == "AAPL"
        assert performance_query.portfolio_id == portfolio_id
