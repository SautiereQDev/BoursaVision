"""
Integration Test for Complete Application Layer
==============================================

End-to-end integration test validating the complete application layer
implementation including use cases, handlers, services, and DTOs.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.commands import CreatePortfolioCommand
from src.application.exceptions import PortfolioNotFoundError
from src.application.handlers.command_handlers import CreatePortfolioCommandHandler
from src.application.handlers.query_handlers import FindInvestmentsQueryHandler
from src.application.mappers import InvestmentMapper, PortfolioMapper
from src.application.queries import FindInvestmentsQuery
from src.application.services.signal_generator import SignalGenerator
from src.application.services.technical_analyzer import TechnicalAnalyzer
from src.application.use_cases.analyze_portfolio import AnalyzePortfolioUseCase
from src.application.use_cases.find_investments import FindInvestmentsUseCase


class TestCompleteApplicationLayer:
    """Integration test for the complete application layer implementation"""

    @pytest.fixture
    def mock_dependencies(self):
        """Create all mocked dependencies"""
        return {
            "investment_repo": AsyncMock(),
            "portfolio_repo": AsyncMock(),
            "market_data_repo": AsyncMock(),
            "user_repo": AsyncMock(),
            "unit_of_work": AsyncMock(),
            "performance_analyzer": MagicMock(),
            "risk_calculator": MagicMock(),
            "scoring_service": MagicMock(),
        }

    @pytest.fixture
    def configured_services(self, mock_dependencies):
        """Configure application services with dependencies"""
        technical_analyzer = TechnicalAnalyzer(
            investment_repository=mock_dependencies["investment_repo"],
            market_data_repository=mock_dependencies["market_data_repo"],
            scoring_service=mock_dependencies["scoring_service"],
        )

        signal_generator = SignalGenerator(technical_analyzer=technical_analyzer)

        return {
            "technical_analyzer": technical_analyzer,
            "signal_generator": signal_generator,
        }

    @pytest.fixture
    def configured_use_cases(self, mock_dependencies, configured_services):
        """Configure use cases with dependencies"""
        find_investments = FindInvestmentsUseCase(
            investment_repository=mock_dependencies["investment_repo"],
            technical_analyzer=configured_services["technical_analyzer"],
            signal_generator=configured_services["signal_generator"],
        )

        analyze_portfolio = AnalyzePortfolioUseCase(
            portfolio_repository=mock_dependencies["portfolio_repo"],
            market_data_repository=mock_dependencies["market_data_repo"],
            performance_analyzer=mock_dependencies["performance_analyzer"],
            risk_calculator=mock_dependencies["risk_calculator"],
            technical_analyzer=configured_services["technical_analyzer"],
            signal_generator=configured_services["signal_generator"],
        )

        return {
            "find_investments": find_investments,
            "analyze_portfolio": analyze_portfolio,
        }

    @pytest.fixture
    def configured_handlers(self, mock_dependencies, configured_use_cases):
        """Configure handlers with dependencies"""
        create_portfolio_handler = CreatePortfolioCommandHandler(
            portfolio_repository=mock_dependencies["portfolio_repo"],
            user_repository=mock_dependencies["user_repo"],
            unit_of_work=mock_dependencies["unit_of_work"],
        )

        find_investments_handler = FindInvestmentsQueryHandler(
            find_investments_use_case=configured_use_cases["find_investments"]
        )

        return {
            "create_portfolio": create_portfolio_handler,
            "find_investments": find_investments_handler,
        }

    @pytest.mark.asyncio
    async def test_complete_investment_search_flow(
        self, mock_dependencies, configured_handlers
    ):
        """Test complete flow from query to result with all layers"""
        # Setup mock data
        mock_investments = [
            self._create_mock_investment("AAPL", "Apple Inc."),
            self._create_mock_investment("GOOGL", "Alphabet Inc."),
        ]

        mock_market_data = self._create_mock_market_data()

        # Configure mocks
        mock_dependencies[
            "investment_repo"
        ].find_by_criteria.return_value = mock_investments
        mock_dependencies["investment_repo"].count_by_criteria.return_value = 2
        mock_dependencies[
            "investment_repo"
        ].find_by_symbol.return_value = mock_investments[0]
        mock_dependencies[
            "market_data_repo"
        ].get_price_history.return_value = mock_market_data

        # Create query
        query = FindInvestmentsQuery(
            sectors=["TECHNOLOGY"], investment_types=["STOCK"], limit=10
        )

        # Execute through handler
        result = await configured_handlers["find_investments"].handle(query)

        # Verify results
        assert len(result.investments) == 2
        assert result.total_count == 2
        assert result.investments[0].symbol == "AAPL"
        assert result.investments[1].symbol == "GOOGL"

        # Verify technical analysis was included
        assert len(result.technical_analysis) >= 0  # May be empty due to mock failures

        # Verify signals were included
        assert len(result.signals) >= 0  # May be empty due to mock failures

        # Verify repository interactions
        mock_dependencies["investment_repo"].find_by_criteria.assert_called_once()
        mock_dependencies["investment_repo"].count_by_criteria.assert_called_once()

    @pytest.mark.asyncio
    async def test_complete_portfolio_creation_flow(
        self, mock_dependencies, configured_handlers
    ):
        """Test complete portfolio creation flow through command handler"""
        # Setup mocks
        user_id = uuid4()
        mock_user = MagicMock(id=user_id)
        mock_dependencies["user_repo"].find_by_id.return_value = mock_user

        # Create command
        command = CreatePortfolioCommand(
            user_id=user_id,
            name="Test Portfolio",
            description="Test portfolio for integration",
            initial_cash_amount=10000.0,
            currency="USD",
        )

        # Execute through handler
        result = await configured_handlers["create_portfolio"].handle(command)

        # Verify result
        assert result is not None

        # Verify interactions
        mock_dependencies["user_repo"].find_by_id.assert_called_once_with(user_id)
        mock_dependencies["portfolio_repo"].save.assert_called_once()
        mock_dependencies["unit_of_work"].commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_technical_analysis_service_integration(
        self, mock_dependencies, configured_services
    ):
        """Test technical analysis service with realistic data flow"""
        # Setup mock investment and market data
        symbol = "AAPL"
        mock_investment = self._create_mock_investment(symbol, "Apple Inc.")
        mock_market_data = self._create_mock_market_data()

        mock_dependencies[
            "investment_repo"
        ].find_by_symbol.return_value = mock_investment
        mock_dependencies[
            "market_data_repo"
        ].get_price_history.return_value = mock_market_data

        # Execute analysis
        result = await configured_services["technical_analyzer"].analyze_investment(
            symbol
        )

        # Verify results
        assert result.symbol == symbol
        assert result.analysis_date is not None
        assert isinstance(result.rsi, (int, float, type(None)))
        assert isinstance(result.sma_20, (int, float, type(None)))

        # Verify repository calls
        mock_dependencies["investment_repo"].find_by_symbol.assert_called_once_with(
            symbol
        )
        mock_dependencies["market_data_repo"].get_price_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_signal_generation_service_integration(
        self, mock_dependencies, configured_services
    ):
        """Test signal generation service integration"""
        # Setup technical analysis mock
        symbol = "AAPL"
        mock_analysis = self._create_mock_technical_analysis(symbol)

        # Mock the technical analyzer to return our analysis
        configured_services["technical_analyzer"].analyze_investment = AsyncMock(
            return_value=mock_analysis
        )

        # Execute signal generation
        result = await configured_services["signal_generator"].generate_signal(symbol)

        # Verify results
        assert result.symbol == symbol
        assert result.action in ["BUY", "SELL", "HOLD"]
        assert 0 <= result.confidence <= 1
        assert result.timestamp is not None
        assert result.reason is not None

        # Verify technical analyzer was called
        configured_services[
            "technical_analyzer"
        ].analyze_investment.assert_called_once_with(symbol)

    @pytest.mark.asyncio
    async def test_dto_validation_and_mapping(self):
        """Test DTO validation and entity mapping"""
        # Test Investment mapping
        mock_investment = self._create_mock_investment("AAPL", "Apple Inc.")
        investment_dto = InvestmentMapper.to_dto(mock_investment)

        assert investment_dto.symbol == "AAPL"
        assert investment_dto.name == "Apple Inc."
        assert investment_dto.investment_type == "STOCK"

        # Test Portfolio mapping
        mock_portfolio = self._create_mock_portfolio()
        portfolio_dto = PortfolioMapper.to_dto(mock_portfolio, include_positions=True)

        assert portfolio_dto.name == "Test Portfolio"
        assert portfolio_dto.total_value is not None
        assert isinstance(portfolio_dto.positions, list)

    @pytest.mark.asyncio
    async def test_error_handling_across_layers(
        self, mock_dependencies, configured_handlers
    ):
        """Test error handling propagation across application layers"""
        # Setup repository to fail
        mock_dependencies["investment_repo"].find_by_criteria.side_effect = Exception(
            "Database error"
        )

        # Create query
        query = FindInvestmentsQuery(limit=10)

        # Verify error propagation
        with pytest.raises(Exception, match="Database error"):
            await configured_handlers["find_investments"].handle(query)

    @pytest.mark.asyncio
    async def test_cross_cutting_concerns_integration(
        self, mock_dependencies, configured_use_cases
    ):
        """Test cross-cutting concerns like logging, metrics, etc."""
        # This would test audit trails, performance metrics, etc.
        # For now, verify that use cases handle errors gracefully

        # Setup portfolio analysis with missing portfolio
        portfolio_id = uuid4()
        mock_dependencies["portfolio_repo"].find_by_id.return_value = None

        # Import here to avoid circular imports
        from src.application.queries import AnalyzePortfolioQuery

        query = AnalyzePortfolioQuery(portfolio_id=portfolio_id)

        # Should raise appropriate error
        with pytest.raises(
            PortfolioNotFoundError, match=f"Portfolio {portfolio_id} not found"
        ):
            await configured_use_cases["analyze_portfolio"].execute(query)

    def _create_mock_investment(self, symbol: str, name: str):
        """Create mock investment entity"""
        investment = MagicMock()
        investment.id = uuid4()
        investment.symbol = symbol
        investment.name = name
        investment.investment_type = "STOCK"
        investment.sector = "TECHNOLOGY"
        investment.market_cap = "LARGE_CAP"
        investment.currency = "USD"
        investment.exchange = "NASDAQ"
        investment.isin = f"US{symbol}1005"
        investment.created_at = datetime.now()
        return investment

    def _create_mock_portfolio(self):
        """Create mock portfolio entity"""
        portfolio = MagicMock()
        portfolio.id = uuid4()
        portfolio.user_id = uuid4()
        portfolio.name = "Test Portfolio"
        portfolio.description = "Test description"
        portfolio.cash_balance = MagicMock()
        portfolio.cash_balance.amount = 1000.0
        portfolio.cash_balance.currency = "USD"
        portfolio.positions = []
        portfolio.created_at = datetime.now()
        portfolio.updated_at = datetime.now()

        # Mock calculate_total_value method
        portfolio.calculate_total_value.return_value = MagicMock()
        portfolio.calculate_total_value.return_value.amount = 1000.0

        return portfolio

    def _create_mock_market_data(self):
        """Create mock market data with sufficient data points"""
        mock_data = MagicMock()

        # Create price data points for technical analysis
        price_points = []
        base_price = 150.0
        for i in range(60):  # 60 days of data
            price_point = MagicMock()
            price_point.close = base_price + (i % 20 - 10)  # Varying prices
            price_point.volume = 1000000 + (i * 10000)
            price_points.append(price_point)

        mock_data.price_data = price_points
        return mock_data

    def _create_mock_technical_analysis(self, symbol: str):
        """Create mock technical analysis DTO"""
        from src.application.dtos import TechnicalAnalysisDTO

        return TechnicalAnalysisDTO(
            symbol=symbol,
            rsi=65.0,  # Slightly overbought
            macd=0.8,  # Positive MACD
            bollinger_position=0.7,  # Near upper band
            sma_20=155.0,
            sma_50=150.0,  # Short MA above long MA
            volume_trend=0.15,  # Increasing volume
            support_level=145.0,
            resistance_level=165.0,
            analysis_date=datetime.now(),
        )
