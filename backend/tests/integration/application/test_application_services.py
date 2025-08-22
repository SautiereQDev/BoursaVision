"""
Integration Tests for Application Services
==========================================

Tests for application services that coordinate domain operations
and orchestrate technical analysis and signal generation.
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.exceptions import AnalysisFailedError
from src.application.services.signal_generator import SignalGenerator
from src.application.services.technical_analyzer import TechnicalAnalyzer


class TestTechnicalAnalyzer:
    """Test suite for TechnicalAnalyzer application service"""

    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories for technical analyzer"""
        investment_repo = AsyncMock()
        market_data_repo = AsyncMock()
        scoring_service = MagicMock()

        return {
            "investment_repo": investment_repo,
            "market_data_repo": market_data_repo,
            "scoring_service": scoring_service,
        }

    @pytest.fixture
    def technical_analyzer(self, mock_repositories):
        """Create TechnicalAnalyzer with mocked dependencies"""
        return TechnicalAnalyzer(
            investment_repository=mock_repositories["investment_repo"],
            market_data_repository=mock_repositories["market_data_repo"],
            scoring_service=mock_repositories["scoring_service"],
        )

    @pytest.mark.asyncio
    async def test_analyze_investment_success(
        self, technical_analyzer, mock_repositories
    ):
        """Test successful investment analysis"""
        # Arrange
        symbol = "AAPL"
        mock_investment = MagicMock()
        mock_market_data = self._create_mock_market_data()

        mock_repositories[
            "investment_repo"
        ].find_by_symbol.return_value = mock_investment
        mock_repositories[
            "market_data_repo"
        ].get_price_history.return_value = mock_market_data

        # Act
        result = await technical_analyzer.analyze_investment(symbol)

        # Assert
        assert result.symbol == symbol
        assert result.rsi is not None
        assert result.sma_20 is not None
        assert result.support_level is not None
        assert result.resistance_level is not None
        assert isinstance(result.analysis_date, datetime)

        # Verify repository calls
        mock_repositories["investment_repo"].find_by_symbol.assert_called_once_with(
            symbol
        )
        mock_repositories["market_data_repo"].get_price_history.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_investment_not_found(
        self, technical_analyzer, mock_repositories
    ):
        """Test analysis when investment not found"""
        # Arrange
        symbol = "INVALID"
        mock_repositories["investment_repo"].find_by_symbol.return_value = None

        # Act & Assert
        with pytest.raises(
            ValueError, match=f"Investment with symbol {symbol} not found"
        ):
            await technical_analyzer.analyze_investment(symbol)

    @pytest.mark.asyncio
    async def test_analyze_investment_insufficient_data(
        self, technical_analyzer, mock_repositories
    ):
        """Test analysis with insufficient market data"""
        # Arrange
        symbol = "AAPL"
        mock_investment = MagicMock()
        mock_market_data = MagicMock()
        mock_market_data.price_data = []  # Empty data

        mock_repositories[
            "investment_repo"
        ].find_by_symbol.return_value = mock_investment
        mock_repositories[
            "market_data_repo"
        ].get_price_history.return_value = mock_market_data

        # Act & Assert
        with pytest.raises(ValueError, match=f"Insufficient market data for {symbol}"):
            await technical_analyzer.analyze_investment(symbol)

    @pytest.mark.asyncio
    async def test_analyze_multiple_investments(
        self, technical_analyzer, mock_repositories
    ):
        """Test analysis of multiple investments"""
        # Arrange
        symbols = ["AAPL", "GOOGL", "INVALID"]

        def mock_find_by_symbol(symbol):
            if symbol == "INVALID":
                return None
            return MagicMock()

        def mock_get_price_history(symbol, **kwargs):
            if symbol == "INVALID":
                return None
            return self._create_mock_market_data()

        mock_repositories[
            "investment_repo"
        ].find_by_symbol.side_effect = mock_find_by_symbol
        mock_repositories[
            "market_data_repo"
        ].get_price_history.side_effect = mock_get_price_history

        # Act
        results = await technical_analyzer.analyze_multiple_investments(symbols)

        # Assert
        assert len(results) == 2  # Only valid symbols
        assert "AAPL" in results
        assert "GOOGL" in results
        assert "INVALID" not in results

    def test_calculate_rsi(self, technical_analyzer):
        """Test RSI calculation"""
        # Arrange
        prices = [
            100,
            102,
            101,
            103,
            104,
            102,
            105,
            107,
            106,
            108,
            110,
            109,
            111,
            113,
            112,
            114,
            116,
            115,
            117,
            119,
        ]

        # Act
        rsi = technical_analyzer._calculate_rsi(prices)

        # Assert
        assert rsi is not None
        assert 0 <= rsi <= 100

    def test_calculate_rsi_insufficient_data(self, technical_analyzer):
        """Test RSI calculation with insufficient data"""
        # Arrange
        prices = [100, 102, 101]  # Less than required period

        # Act
        rsi = technical_analyzer._calculate_rsi(prices)

        # Assert
        assert rsi is None

    def test_calculate_bollinger_position(self, technical_analyzer):
        """Test Bollinger Bands position calculation"""
        # Arrange
        prices = [100] * 20 + [110]  # Prices with recent spike

        # Act
        position = technical_analyzer._calculate_bollinger_position(prices)

        # Assert
        assert position is not None
        assert 0 <= position <= 1

    def _create_mock_market_data(self):
        """Create mock market data with sufficient price points"""
        mock_data = MagicMock()

        # Create mock price data points
        price_points = []
        base_price = 150.0
        for i in range(50):  # Sufficient data for analysis
            price_point = MagicMock()
            price_point.close = base_price + (i % 10 - 5)  # Varying prices
            price_point.volume = 1000000 + (i * 10000)
            price_points.append(price_point)

        mock_data.price_data = price_points
        return mock_data


class TestSignalGenerator:
    """Test suite for SignalGenerator application service"""

    @pytest.fixture
    def mock_technical_analyzer(self):
        """Mock technical analyzer for signal generator"""
        analyzer = AsyncMock(spec=TechnicalAnalyzer)
        return analyzer

    @pytest.fixture
    def signal_generator(self, mock_technical_analyzer):
        """Create SignalGenerator with mocked dependencies"""
        return SignalGenerator(technical_analyzer=mock_technical_analyzer)

    @pytest.mark.asyncio
    async def test_generate_signal_buy(self, signal_generator, mock_technical_analyzer):
        """Test buy signal generation"""
        # Arrange
        symbol = "AAPL"
        mock_analysis = self._create_mock_analysis(
            symbol=symbol,
            rsi=25.0,  # Oversold
            sma_20=150.0,
            sma_50=145.0,  # Short MA above long MA
            macd=0.5,  # Positive MACD
            bollinger_position=0.1,  # Near lower band
        )

        mock_technical_analyzer.analyze_investment.return_value = mock_analysis

        # Act
        result = await signal_generator.generate_signal(symbol)

        # Assert
        assert result.symbol == symbol
        assert result.action == "BUY"
        assert result.confidence > 0.5
        assert "RSI oversold" in result.reason
        assert "rsi" in result.metadata

    @pytest.mark.asyncio
    async def test_generate_signal_sell(
        self, signal_generator, mock_technical_analyzer
    ):
        """Test sell signal generation"""
        # Arrange
        symbol = "AAPL"
        mock_analysis = self._create_mock_analysis(
            symbol=symbol,
            rsi=80.0,  # Overbought
            sma_20=145.0,
            sma_50=150.0,  # Short MA below long MA
            macd=-0.5,  # Negative MACD
            bollinger_position=0.9,  # Near upper band
        )

        mock_technical_analyzer.analyze_investment.return_value = mock_analysis

        # Act
        result = await signal_generator.generate_signal(symbol)

        # Assert
        assert result.symbol == symbol
        assert result.action == "SELL"
        assert result.confidence > 0.5
        assert "RSI overbought" in result.reason

    @pytest.mark.asyncio
    async def test_generate_signal_hold(
        self, signal_generator, mock_technical_analyzer
    ):
        """Test hold signal generation"""
        # Arrange
        symbol = "AAPL"
        mock_analysis = self._create_mock_analysis(
            symbol=symbol,
            rsi=50.0,  # Neutral
            sma_20=150.0,
            sma_50=150.0,  # Equal MAs
            macd=0.0,  # Neutral MACD
            bollinger_position=0.5,  # Middle of bands
        )

        mock_technical_analyzer.analyze_investment.return_value = mock_analysis

        # Act
        result = await signal_generator.generate_signal(symbol)

        # Assert
        assert result.symbol == symbol
        assert result.action == "HOLD"
        assert result.confidence <= 0.5

    @pytest.mark.asyncio
    async def test_generate_signals_for_portfolio(
        self, signal_generator, mock_technical_analyzer
    ):
        """Test signal generation for portfolio"""
        # Arrange
        symbols = ["AAPL", "GOOGL"]

        def mock_analyze_investment(symbol):
            return self._create_mock_analysis(
                symbol=symbol,
                rsi=30.0 if symbol == "AAPL" else 70.0,
                sma_20=150.0
                if symbol == "AAPL"
                else 140.0,  # GOOGL: 140 < 145 = SELL signal
                sma_50=145.0,
            )

        mock_technical_analyzer.analyze_investment.side_effect = mock_analyze_investment

        # Act
        results = await signal_generator.generate_signals_for_portfolio(symbols)

        # Assert
        assert len(results) == 2
        assert "AAPL" in results
        assert "GOOGL" in results
        assert results["AAPL"].action == "BUY"  # Oversold RSI
        assert results["GOOGL"].action == "SELL"  # Overbought RSI

    @pytest.mark.asyncio
    async def test_generate_signals_handles_errors(
        self, signal_generator, mock_technical_analyzer
    ):
        """Test signal generation handles analysis errors gracefully"""
        # Arrange
        symbols = ["AAPL", "INVALID"]

        def mock_analyze_investment(symbol):
            if symbol == "INVALID":
                raise AnalysisFailedError("Analysis failed")
            return self._create_mock_analysis(symbol=symbol)

        mock_technical_analyzer.analyze_investment.side_effect = mock_analyze_investment

        # Act
        results = await signal_generator.generate_signals_for_portfolio(symbols)

        # Assert
        assert len(results) == 1  # Only successful analysis
        assert "AAPL" in results
        assert "INVALID" not in results

    def _create_mock_analysis(self, symbol="AAPL", **kwargs):
        """Create mock technical analysis DTO"""
        from src.application.dtos import TechnicalAnalysisDTO

        defaults = {
            "symbol": symbol,
            "rsi": 50.0,
            "macd": 0.0,
            "bollinger_position": 0.5,
            "sma_20": 150.0,
            "sma_50": 150.0,
            "volume_trend": 0.0,
            "support_level": 140.0,
            "resistance_level": 160.0,
            "analysis_date": datetime.now(),
        }

        defaults.update(kwargs)
        return TechnicalAnalysisDTO(**defaults)
