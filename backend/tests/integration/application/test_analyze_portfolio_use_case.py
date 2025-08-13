"""
Integration Tests for Analyze Portfolio Use Case
===============================================

Tests the complete flow of portfolio analysis including
performance calculation, risk analysis, and recommendations.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.exceptions import PortfolioNotFoundError
from src.application.queries import AnalyzePortfolioQuery
from src.application.services.signal_generator import SignalGenerator
from src.application.services.technical_analyzer import TechnicalAnalyzer
from src.application.use_cases.analyze_portfolio import AnalyzePortfolioUseCase


class TestAnalyzePortfolioUseCase:
    """Test suite for AnalyzePortfolioUseCase"""

    @pytest.fixture
    def mock_portfolio_repository(self):
        """Mock portfolio repository"""
        repository = AsyncMock()

        async def mock_find_by_id(portfolio_id):
            portfolio = self._create_mock_portfolio()
            portfolio.id = portfolio_id  # Use the ID from the request
            return portfolio

        repository.find_by_id.side_effect = mock_find_by_id
        return repository

    @pytest.fixture
    def mock_market_data_repository(self):
        """Mock market data repository"""
        repository = AsyncMock()
        repository.get_price_history.return_value = self._create_mock_market_data()
        return repository

    @pytest.fixture
    def mock_performance_analyzer(self):
        """Mock performance analyzer domain service"""
        analyzer = MagicMock()
        analyzer.calculate_performance.return_value = self._create_mock_performance()
        analyzer.compare_to_benchmark.return_value = (
            self._create_mock_benchmark_comparison()
        )
        return analyzer

    @pytest.fixture
    def mock_risk_calculator(self):
        """Mock risk calculator domain service"""
        calculator = MagicMock()
        calculator.calculate_portfolio_risk.return_value = (
            self._create_mock_risk_metrics()
        )
        return calculator

    @pytest.fixture
    def mock_technical_analyzer(self):
        """Mock technical analyzer application service"""
        analyzer = AsyncMock(spec=TechnicalAnalyzer)
        return analyzer

    @pytest.fixture
    def mock_signal_generator(self):
        """Mock signal generator application service"""
        generator = AsyncMock(spec=SignalGenerator)
        generator.generate_signals_for_portfolio.return_value = {
            "AAPL": self._create_mock_signal("AAPL", "BUY"),
            "GOOGL": self._create_mock_signal("GOOGL", "SELL"),
        }
        return generator

    @pytest.fixture
    def use_case(
        self,
        mock_portfolio_repository,
        mock_market_data_repository,
        mock_performance_analyzer,
        mock_risk_calculator,
        mock_technical_analyzer,
        mock_signal_generator,
    ):
        """Create use case instance with mocked dependencies"""
        return AnalyzePortfolioUseCase(
            portfolio_repository=mock_portfolio_repository,
            market_data_repository=mock_market_data_repository,
            performance_analyzer=mock_performance_analyzer,
            risk_calculator=mock_risk_calculator,
            technical_analyzer=mock_technical_analyzer,
            signal_generator=mock_signal_generator,
        )

    @pytest.mark.asyncio
    async def test_execute_basic_analysis(self, use_case, mock_portfolio_repository):
        """Test basic portfolio analysis"""
        # Arrange
        portfolio_id = uuid4()
        query = AnalyzePortfolioQuery(
            portfolio_id=portfolio_id, include_technical_analysis=True
        )

        # Act
        result = await use_case.execute(query)

        # Assert
        assert result.portfolio.id == portfolio_id
        assert result.performance.total_return == 15.0
        assert result.performance.sharpe_ratio == 1.2
        assert len(result.risk_metrics) > 0
        assert len(result.allocation) > 0
        assert len(result.recommendations) > 0
        assert len(result.signals) == 2

        # Verify portfolio was fetched
        mock_portfolio_repository.find_by_id.assert_called_once_with(portfolio_id)

    @pytest.mark.asyncio
    async def test_execute_with_date_range(self, use_case, mock_performance_analyzer):
        """Test portfolio analysis with custom date range"""
        # Arrange
        portfolio_id = uuid4()
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now()

        query = AnalyzePortfolioQuery(
            portfolio_id=portfolio_id,
            start_date=start_date,
            end_date=end_date,
            include_technical_analysis=False,
        )

        # Act
        result = await use_case.execute(query)

        # Assert
        assert result.portfolio.id == portfolio_id
        assert len(result.signals) == 0  # Technical analysis disabled

        # Verify performance analyzer was called with correct dates
        mock_performance_analyzer.calculate_performance.assert_called_once()
        call_args = mock_performance_analyzer.calculate_performance.call_args
        assert call_args[0][1] == start_date  # start_date parameter
        assert call_args[0][2] == end_date  # end_date parameter

    @pytest.mark.asyncio
    async def test_execute_with_benchmark_comparison(
        self, use_case, mock_market_data_repository, mock_performance_analyzer
    ):
        """Test portfolio analysis with benchmark comparison"""
        # Arrange
        portfolio_id = uuid4()
        benchmark_symbol = "SPY"

        query = AnalyzePortfolioQuery(
            portfolio_id=portfolio_id,
            benchmark_symbol=benchmark_symbol,
            include_technical_analysis=False,
        )

        # Act
        result = await use_case.execute(query)

        # Assert
        assert result.performance.alpha == 2.5
        assert result.performance.beta == 1.1

        # Verify benchmark data was fetched
        mock_market_data_repository.get_price_history.assert_called()

        # Verify benchmark comparison was performed
        mock_performance_analyzer.compare_to_benchmark.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_portfolio_not_found(
        self, use_case, mock_portfolio_repository
    ):
        """Test handling of non-existent portfolio"""
        # Arrange
        portfolio_id = uuid4()
        mock_portfolio_repository.find_by_id.side_effect = None
        mock_portfolio_repository.find_by_id.return_value = None

        query = AnalyzePortfolioQuery(portfolio_id=portfolio_id)

        # Act & Assert
        with pytest.raises(
            PortfolioNotFoundError, match=f"Portfolio {portfolio_id} not found"
        ):
            await use_case.execute(query)

    @pytest.mark.asyncio
    async def test_calculate_asset_allocation(self, use_case):
        """Test asset allocation calculation"""
        # Arrange
        query = AnalyzePortfolioQuery(
            portfolio_id=uuid4(), include_technical_analysis=False
        )

        # Act
        result = await use_case.execute(query)

        # Assert
        allocation = result.allocation
        assert "AAPL" in allocation
        assert "GOOGL" in allocation
        assert "CASH" in allocation

        # Verify percentages sum to approximately 100%
        total_allocation = sum(allocation.values())
        assert abs(total_allocation - 100.0) < 0.01

    @pytest.mark.asyncio
    async def test_generate_recommendations(self, use_case):
        """Test investment recommendations generation"""
        # Arrange
        query = AnalyzePortfolioQuery(
            portfolio_id=uuid4(), include_technical_analysis=False
        )

        # Act
        result = await use_case.execute(query)

        # Assert
        recommendations = result.recommendations
        assert len(recommendations) > 0
        assert any("diversifying" in rec.lower() for rec in recommendations)

    @pytest.mark.asyncio
    async def test_risk_metrics_calculation(self, use_case, mock_risk_calculator):
        """Test risk metrics calculation"""
        # Arrange
        query = AnalyzePortfolioQuery(
            portfolio_id=uuid4(), include_technical_analysis=False
        )

        # Act
        result = await use_case.execute(query)

        # Assert
        risk_metrics = result.risk_metrics
        assert "beta" in risk_metrics
        assert "value_at_risk_95" in risk_metrics
        assert "concentration_risk" in risk_metrics

        # Verify risk calculator was called
        mock_risk_calculator.calculate_portfolio_risk.assert_called_once()

    @pytest.mark.asyncio
    async def test_signals_generation_when_enabled(
        self, use_case, mock_signal_generator
    ):
        """Test trading signals generation when technical analysis is enabled"""
        # Arrange
        query = AnalyzePortfolioQuery(
            portfolio_id=uuid4(), include_technical_analysis=True
        )

        # Act
        result = await use_case.execute(query)

        # Assert
        assert len(result.signals) == 2
        signal_actions = [signal.action for signal in result.signals]
        assert "BUY" in signal_actions
        assert "SELL" in signal_actions

        # Verify signal generator was called
        mock_signal_generator.generate_signals_for_portfolio.assert_called_once()

    def _create_mock_portfolio(self):
        """Create mock portfolio entity"""
        portfolio = MagicMock()
        portfolio.id = uuid4()
        portfolio.user_id = uuid4()
        portfolio.name = "Test Portfolio"
        portfolio.description = "Test portfolio for analysis"

        # Mock positions
        position1 = MagicMock()
        position1.symbol = "AAPL"
        position1.quantity = 10
        position1.average_price = MagicMock()
        position1.average_price.amount = 150.0
        position1.calculate_market_value.return_value = MagicMock(amount=1500.0)

        position2 = MagicMock()
        position2.symbol = "GOOGL"
        position2.quantity = 5
        position2.average_price = MagicMock()
        position2.average_price.amount = 2000.0
        position2.calculate_market_value.return_value = MagicMock(amount=10000.0)

        portfolio.positions = [position1, position2]

        # Mock cash balance
        portfolio.cash_balance = MagicMock()
        portfolio.cash_balance.amount = 500.0

        # Mock total value calculation
        portfolio.calculate_total_value.return_value = MagicMock(amount=12000.0)

        portfolio.created_at = datetime.now()
        portfolio.updated_at = datetime.now()

        return portfolio

    def _create_mock_market_data(self):
        """Create mock market data"""
        market_data = MagicMock()
        market_data.price_data = []
        return market_data

    def _create_mock_performance(self):
        """Create mock performance metrics"""
        performance = MagicMock()
        performance.total_return = 15.0
        performance.annualized_return = 12.5
        performance.volatility = 18.2
        performance.sharpe_ratio = 1.2
        performance.max_drawdown = -5.5
        return performance

    def _create_mock_benchmark_comparison(self):
        """Create mock benchmark comparison"""
        comparison = MagicMock()
        comparison.alpha = 2.5
        comparison.beta = 1.1
        return comparison

    def _create_mock_risk_metrics(self):
        """Create mock risk metrics"""
        risk_metrics = MagicMock()
        risk_metrics.beta = 1.1
        risk_metrics.correlation_spy = 0.85
        risk_metrics.concentration_risk = 0.25
        risk_metrics.sector_concentration = 0.60
        risk_metrics.value_at_risk_95 = -3.2
        risk_metrics.expected_shortfall = -4.8
        return risk_metrics

    def _create_mock_signal(self, symbol, action):
        """Create mock signal DTO"""
        from src.application.dtos import SignalDTO

        return SignalDTO(
            symbol=symbol,
            action=action,
            confidence=0.75,
            price=150.0,
            timestamp=datetime.now(),
            reason=f"Technical analysis suggests {action}",
            metadata={"rsi": 45.0},
        )
