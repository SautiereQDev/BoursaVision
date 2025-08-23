"""
Coverage tests for AnalyzePortfolio Use Case - Phase 2
======================================================
Targeted tests to improve coverage from 92.1% to 98%+

Focuses on missing lines: 79-98, 169->176, 207->203, 256->259, 351->354
"""

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, Mock
from uuid import uuid4

import pytest

from boursa_vision.application.dtos import (
    MoneyDTO,
    PerformanceMetricsDTO,
    PortfolioAnalysisResultDTO,
    PortfolioDTO,
)
from boursa_vision.application.exceptions import PortfolioNotFoundError
from boursa_vision.application.queries.portfolio.analyze_portfolio_query import (
    AnalyzePortfolioQuery,
)
from boursa_vision.application.use_cases.analyze_portfolio import (
    AnalyzePortfolioUseCase,
)
from boursa_vision.domain.value_objects.money import Currency, Money


@pytest.fixture
def mock_repositories():
    """Mock repositories fixture."""
    portfolio_repo = AsyncMock()
    market_data_repo = AsyncMock()
    return portfolio_repo, market_data_repo


@pytest.fixture
def mock_services():
    """Mock services fixture."""
    performance_analyzer = Mock()
    risk_calculator = Mock()
    technical_analyzer = Mock()
    signal_generator = AsyncMock()  # Change to AsyncMock for await support
    return performance_analyzer, risk_calculator, technical_analyzer, signal_generator


@pytest.fixture
def analyze_portfolio_use_case(mock_repositories, mock_services):
    """AnalyzePortfolioUseCase fixture."""
    portfolio_repo, market_data_repo = mock_repositories
    (
        performance_analyzer,
        risk_calculator,
        technical_analyzer,
        signal_generator,
    ) = mock_services

    return AnalyzePortfolioUseCase(
        portfolio_repository=portfolio_repo,
        market_data_repository=market_data_repo,
        performance_analyzer=performance_analyzer,
        risk_calculator=risk_calculator,
        technical_analyzer=technical_analyzer,
        signal_generator=signal_generator,
    )


class TestAnalyzePortfolioCoverage:
    """Test coverage improvements for AnalyzePortfolioUseCase"""

    async def test_calculate_performance_without_model_dump(
        self, analyze_portfolio_use_case, mock_repositories
    ):
        """Test performance calculation when object doesn't have model_dump (lines 79-98)"""
        portfolio_repo, market_data_repo = mock_repositories

        # Create mock portfolio
        mock_portfolio = Mock()
        mock_portfolio.id = uuid4()
        mock_portfolio.positions = []

        # Mock calculate_total_value to return proper Money object
        mock_money = Money(Decimal("10000.0"), Currency.USD)
        mock_portfolio.calculate_total_value.return_value = mock_money

        portfolio_repo.get_by_id.return_value = mock_portfolio

        # Mock performance analyzer to return object without model_dump
        mock_performance = Mock(spec=[])  # No model_dump method
        mock_performance.total_return = 10.5
        mock_performance.annualized_return = 12.3
        mock_performance.volatility = 15.2
        mock_performance.sharpe_ratio = 0.8
        mock_performance.max_drawdown = -8.5
        mock_performance.alpha = 2.1
        mock_performance.beta = 1.2

        analyze_portfolio_use_case._performance_analyzer.calculate_performance.return_value = (
            mock_performance
        )

        # Create query
        query = AnalyzePortfolioQuery(portfolio_id=mock_portfolio.id)

        # Execute - should hit the getattr branch without model_dump
        result = await analyze_portfolio_use_case._calculate_performance_metrics(
            mock_portfolio, datetime(2024, 1, 1), datetime(2024, 12, 31)
        )

        # Verify the DTO was created correctly from getattr calls
        assert isinstance(result, PerformanceMetricsDTO)
        assert result.total_return == 10.5
        assert result.annualized_return == 12.3

    async def test_calculate_performance_with_benchmark_no_data(
        self, analyze_portfolio_use_case, mock_repositories
    ):
        """Test benchmark comparison when no benchmark data available (lines 169->176)"""
        portfolio_repo, market_data_repo = mock_repositories

        # Setup mock portfolio
        mock_portfolio = Mock()
        mock_portfolio.id = uuid4()
        mock_portfolio.positions = []

        # Mock calculate_total_value to return proper Money object
        mock_money = Money(Decimal("10000.0"), Currency.USD)
        mock_portfolio.calculate_total_value.return_value = mock_money

        portfolio_repo.get_by_id.return_value = mock_portfolio

        # Setup market data repo to return None for benchmark
        market_data_repo.get_price_history.return_value = None

        # Mock performance analyzer
        mock_performance = Mock()
        mock_performance.total_return = 10.5
        mock_performance.annualized_return = 12.3
        mock_performance.volatility = 15.2
        mock_performance.sharpe_ratio = 0.8
        mock_performance.max_drawdown = -8.5
        mock_performance.var_95 = -5.2  # Add missing var_95

        analyze_portfolio_use_case._performance_analyzer.calculate_performance.return_value = (
            mock_performance
        )

        # Execute with benchmark but no data available
        result = await analyze_portfolio_use_case._calculate_performance_metrics(
            mock_portfolio,
            datetime(2024, 1, 1),
            datetime(2024, 12, 31),
            benchmark_symbol="SPY",
        )

        # Should have None for alpha/beta when no benchmark data
        assert result.alpha is None
        assert result.beta is None

    async def test_calculate_risk_metrics_no_market_data(
        self, analyze_portfolio_use_case, mock_repositories
    ):
        """Test risk calculation when no market data available (line 207->203)"""
        portfolio_repo, market_data_repo = mock_repositories

        # Create mock portfolio with positions
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.quantity = 100
        mock_position.purchase_price = Money(Decimal("150.00"), Currency.USD)

        mock_portfolio = Mock()
        mock_portfolio.positions = [mock_position]

        # Market data returns None (no data available)
        market_data_repo.get_price_history.return_value = None

        # Execute
        result = await analyze_portfolio_use_case._calculate_risk_metrics(
            mock_portfolio, datetime(2024, 1, 1), datetime(2024, 12, 31)
        )

        # Should handle gracefully with empty positions_data
        analyze_portfolio_use_case._risk_calculator.calculate_portfolio_risk.assert_called_with(
            []
        )

    def test_calculate_allocation_with_cash_balance_zero(
        self, analyze_portfolio_use_case, mock_repositories
    ):
        """Test allocation calculation when cash balance is zero (line 256->259)"""
        portfolio_repo, market_data_repo = mock_repositories

        # Create position with market value
        mock_position = Mock()
        mock_position.symbol = "AAPL"
        mock_position.quantity = 100
        mock_position.average_price = Money(Decimal("150.00"), Currency.USD)

        # Mock calculate_market_value for position
        position_market_value = Money(Decimal("15500.00"), Currency.USD)
        mock_position.calculate_market_value.return_value = position_market_value

        mock_portfolio = Mock()
        mock_portfolio.positions = [mock_position]
        mock_portfolio.cash_balance = Money(Decimal("0.00"), Currency.USD)  # Zero cash

        # Mock calculate_total_value for portfolio
        total_value = Money(Decimal("15500.00"), Currency.USD)
        mock_portfolio.calculate_total_value.return_value = total_value

        # Execute
        result = analyze_portfolio_use_case._calculate_asset_allocation(mock_portfolio)

        # Should not include CASH in allocation when balance is 0
        assert "CASH" not in result
        assert "AAPL" in result
        assert result["AAPL"] == 100.0  # 100% since no cash

    def test_convert_portfolio_to_dto_with_mock_attributes(
        self, analyze_portfolio_use_case
    ):
        """Test portfolio DTO conversion with mock attributes (lines 351->354)"""
        # Create portfolio with MagicMock attributes to trigger mock detection
        mock_portfolio = Mock()
        mock_portfolio.id = uuid4()
        mock_portfolio.user_id = uuid4()
        mock_portfolio.name = "Test Portfolio"
        mock_portfolio.description = "Test Description"

        # Set currency as MagicMock to trigger the mock detection branch
        mock_portfolio.currency = MagicMock()
        mock_portfolio.currency._mock_name = "currency_mock"

        # Set cash_balance as MagicMock to trigger the mock detection branch
        mock_portfolio.cash_balance = MagicMock()
        mock_portfolio.cash_balance._mock_name = "cash_balance_mock"

        mock_portfolio.positions = []
        mock_portfolio.created_at = datetime.now()
        mock_portfolio.updated_at = datetime.now()

        # Execute
        result = analyze_portfolio_use_case._map_portfolio_to_dto(mock_portfolio)

        # Should use default values when mocks detected
        assert result.currency == "USD"
        assert result.total_value.amount == 0.0

    async def test_handle_missing_portfolio_data(
        self, analyze_portfolio_use_case, mock_repositories
    ):
        """Test handling when portfolio has missing data attributes"""
        portfolio_repo, _ = mock_repositories

        # Create minimal portfolio missing some attributes
        mock_portfolio = Mock()  # Remove spec=[] to allow dynamic attributes
        mock_portfolio.id = uuid4()
        mock_portfolio.user_id = uuid4()
        mock_portfolio.name = "Test Portfolio"
        mock_portfolio.description = "Test Description"
        mock_portfolio.created_at = datetime.now()
        mock_portfolio.updated_at = datetime.now()
        mock_portfolio.positions = []

        # Mock calculate_total_value to return proper Money object
        mock_money = Money(Decimal("1000.0"), Currency.USD)
        mock_portfolio.calculate_total_value.return_value = mock_money

        # Add cash_balance for asset allocation calculation
        mock_cash_balance = Mock()
        mock_cash_balance._mock_name = "cash_balance_mock"  # Trigger mock detection
        mock_cash_balance.amount = 100.0  # For _calculate_asset_allocation
        mock_portfolio.cash_balance = mock_cash_balance

        # Missing cash_balance, currency, etc.

        portfolio_repo.find_by_id.return_value = mock_portfolio

        # Mock performance analyzer
        mock_performance = Mock()
        mock_performance.total_return = 0.0
        mock_performance.annualized_return = 0.0
        mock_performance.volatility = 0.0
        mock_performance.sharpe_ratio = 0.0
        mock_performance.max_drawdown = 0.0
        mock_performance.var_95 = 0.0  # Add missing var_95

        analyze_portfolio_use_case._performance_analyzer.calculate_performance.return_value = (
            mock_performance
        )
        analyze_portfolio_use_case._risk_calculator.calculate_portfolio_risk.return_value = Mock(
            var_95=0.0,
            expected_shortfall=0.0,
            beta=1.0,
            correlation_with_market=0.0,
            correlation_spy=0.0,
            concentration_risk=0.0,
            sector_concentration=0.0,
            value_at_risk_95=0.0,
        )

        # Configure signal generator to return empty dict
        analyze_portfolio_use_case._signal_generator.generate_signals_for_portfolio.return_value = (
            {}
        )

        # Execute
        query = AnalyzePortfolioQuery(portfolio_id=mock_portfolio.id)
        result = await analyze_portfolio_use_case.execute(query)

        # Should handle gracefully
        assert isinstance(result, PortfolioAnalysisResultDTO)

    async def test_performance_calculation_edge_cases(
        self, analyze_portfolio_use_case, mock_repositories
    ):
        """Test performance calculation with edge case values"""
        portfolio_repo, market_data_repo = mock_repositories

        # Create portfolio
        mock_portfolio = Mock()
        mock_portfolio.id = uuid4()
        mock_portfolio.positions = []

        # Mock calculate_total_value to return proper Money object
        mock_money = Money(Decimal("5000.0"), Currency.USD)
        mock_portfolio.calculate_total_value.return_value = mock_money

        portfolio_repo.get_by_id.return_value = mock_portfolio

        # Mock performance with None/missing values
        mock_performance = Mock()
        mock_performance.total_return = 0.0  # Should default to 0.0
        mock_performance.annualized_return = 0.0
        mock_performance.volatility = 0.0
        mock_performance.sharpe_ratio = 0.0
        mock_performance.max_drawdown = 0.0
        mock_performance.alpha = 0.0
        mock_performance.beta = 0.0
        mock_performance.var_95 = 0.0

        analyze_portfolio_use_case._performance_analyzer.calculate_performance.return_value = (
            mock_performance
        )

        # Execute
        result = await analyze_portfolio_use_case._calculate_performance_metrics(
            mock_portfolio, datetime(2024, 1, 1), datetime(2024, 12, 31)
        )

        # Should handle None values gracefully
        assert result.total_return == 0.0
        assert result.annualized_return == 0.0
        assert result.volatility == 0.0
        assert result.sharpe_ratio == 0.0
        assert result.max_drawdown == 0.0
