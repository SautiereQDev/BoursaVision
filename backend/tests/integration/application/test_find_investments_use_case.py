"""
Integration Tests for Find Investments Use Case
===============================================

Tests the complete flow of finding investments including
technical analysis and signal generation.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.queries import FindInvestmentsQuery
from src.application.services.signal_generator import SignalGenerator
from src.application.services.technical_analyzer import TechnicalAnalyzer
from src.application.use_cases.find_investments import FindInvestmentsUseCase


class TestFindInvestmentsUseCase:
    """Test suite for FindInvestmentsUseCase"""

    @pytest.fixture
    def mock_investment_repository(self):
        """Mock investment repository"""
        repository = AsyncMock()
        repository.find_by_criteria.return_value = self._create_mock_investments()
        repository.count_by_criteria.return_value = 2
        return repository

    @pytest.fixture
    def mock_technical_analyzer(self):
        """Mock technical analyzer"""
        analyzer = AsyncMock(spec=TechnicalAnalyzer)
        analyzer.analyze_multiple_investments.return_value = {
            "AAPL": self._create_mock_technical_analysis("AAPL"),
            "GOOGL": self._create_mock_technical_analysis("GOOGL"),
        }
        return analyzer

    @pytest.fixture
    def mock_signal_generator(self):
        """Mock signal generator"""
        generator = AsyncMock(spec=SignalGenerator)
        generator.generate_signals_for_portfolio.return_value = {
            "AAPL": self._create_mock_signal("AAPL", "BUY"),
            "GOOGL": self._create_mock_signal("GOOGL", "HOLD"),
        }
        return generator

    @pytest.fixture
    def use_case(
        self, mock_investment_repository, mock_technical_analyzer, mock_signal_generator
    ):
        """Create use case instance with mocked dependencies"""
        return FindInvestmentsUseCase(
            investment_repository=mock_investment_repository,
            technical_analyzer=mock_technical_analyzer,
            signal_generator=mock_signal_generator,
        )

    @pytest.mark.asyncio
    async def test_execute_basic_search(self, use_case, mock_investment_repository):
        """Test basic investment search without filters"""
        # Arrange
        query = FindInvestmentsQuery(limit=10, offset=0)

        # Act
        result = await use_case.execute(query)

        # Assert
        assert len(result.investments) == 2
        assert result.total_count == 2
        assert "AAPL" in [inv.symbol for inv in result.investments]
        assert "GOOGL" in [inv.symbol for inv in result.investments]

        # Verify repository was called with correct parameters
        mock_investment_repository.find_by_criteria.assert_called_once()
        call_args = mock_investment_repository.find_by_criteria.call_args
        assert call_args[1]["limit"] == 10
        assert call_args[1]["offset"] == 0

    @pytest.mark.asyncio
    async def test_execute_with_filters(self, use_case, mock_investment_repository):
        """Test investment search with filters"""
        # Arrange
        query = FindInvestmentsQuery(
            sectors=["TECHNOLOGY"],
            investment_types=["STOCK"],
            currency="USD",
            min_price=100.0,
            max_price=200.0,
            search_term="Apple",
            limit=20,
            offset=10,
        )

        # Act
        result = await use_case.execute(query)

        # Assert
        assert len(result.investments) == 2

        # Verify repository was called with filters
        call_args = mock_investment_repository.find_by_criteria.call_args
        criteria = call_args[1]["criteria"]
        assert criteria["sectors"] == ["TECHNOLOGY"]
        assert criteria["investment_types"] == ["STOCK"]
        assert criteria["currency"] == "USD"
        assert criteria["price_range"] == (100.0, 200.0)
        assert criteria["search_term"] == "Apple"

    @pytest.mark.asyncio
    async def test_execute_includes_technical_analysis(
        self, use_case, mock_technical_analyzer
    ):
        """Test that technical analysis is included in results"""
        # Arrange
        query = FindInvestmentsQuery()

        # Act
        result = await use_case.execute(query)

        # Assert
        assert len(result.technical_analysis) == 2
        symbols = [ta.symbol for ta in result.technical_analysis]
        assert "AAPL" in symbols
        assert "GOOGL" in symbols

        # Verify technical analyzer was called
        mock_technical_analyzer.analyze_multiple_investments.assert_called_once()
        call_args = mock_technical_analyzer.analyze_multiple_investments.call_args
        symbols = call_args[0][0]
        assert "AAPL" in symbols
        assert "GOOGL" in symbols

    @pytest.mark.asyncio
    async def test_execute_includes_signals(self, use_case, mock_signal_generator):
        """Test that trading signals are included in results"""
        # Arrange
        query = FindInvestmentsQuery()

        # Act
        result = await use_case.execute(query)

        # Assert
        assert len(result.signals) == 2
        signal_symbols = [sig.symbol for sig in result.signals]
        assert "AAPL" in signal_symbols
        assert "GOOGL" in signal_symbols

        # Check specific signals
        signals_by_symbol = {sig.symbol: sig for sig in result.signals}
        assert signals_by_symbol["AAPL"].action == "BUY"
        assert signals_by_symbol["GOOGL"].action == "HOLD"

        # Verify signal generator was called
        mock_signal_generator.generate_signals_for_portfolio.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_handles_technical_analysis_failure(
        self, use_case, mock_technical_analyzer
    ):
        """Test graceful handling of technical analysis failures"""
        # Arrange
        query = FindInvestmentsQuery()
        mock_technical_analyzer.analyze_multiple_investments.side_effect = Exception(
            "Analysis failed"
        )

        # Act
        result = await use_case.execute(query)

        # Assert
        assert len(result.investments) == 2  # Investments still returned
        assert len(result.technical_analysis) == 0  # Empty due to failure
        assert len(result.signals) == 2  # Signals still work

    @pytest.mark.asyncio
    async def test_execute_handles_signal_generation_failure(
        self, use_case, mock_signal_generator
    ):
        """Test graceful handling of signal generation failures"""
        # Arrange
        query = FindInvestmentsQuery()
        mock_signal_generator.generate_signals_for_portfolio.side_effect = Exception(
            "Signal generation failed"
        )

        # Act
        result = await use_case.execute(query)

        # Assert
        assert len(result.investments) == 2  # Investments still returned
        assert len(result.technical_analysis) == 2  # Technical analysis still works
        assert len(result.signals) == 0  # Empty due to failure

    def _create_mock_investments(self):
        """Create mock investment entities"""
        return [
            MagicMock(
                id=uuid4(),
                symbol="AAPL",
                name="Apple Inc.",
                investment_type="STOCK",
                sector="TECHNOLOGY",
                market_cap="LARGE_CAP",
                currency="USD",
                exchange="NASDAQ",
                isin="US0378331005",
                created_at=datetime.now(),
            ),
            MagicMock(
                id=uuid4(),
                symbol="GOOGL",
                name="Alphabet Inc.",
                investment_type="STOCK",
                sector="TECHNOLOGY",
                market_cap="LARGE_CAP",
                currency="USD",
                exchange="NASDAQ",
                isin="US02079K3059",
                created_at=datetime.now(),
            ),
        ]

    def _create_mock_technical_analysis(self, symbol):
        """Create mock technical analysis DTO"""
        from src.application.dtos import TechnicalAnalysisDTO

        return TechnicalAnalysisDTO(
            symbol=symbol,
            rsi=45.0,
            macd=0.5,
            bollinger_position=0.6,
            sma_20=150.0,
            sma_50=145.0,
            volume_trend=0.1,
            support_level=140.0,
            resistance_level=160.0,
            analysis_date=datetime.now(),
        )

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
            metadata={"rsi": 45.0, "macd": 0.5},
        )
