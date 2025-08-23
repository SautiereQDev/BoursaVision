"""
Unit tests for SignalGenerator service.

Tests the SignalGenerator application service following AAA (Arrange-Act-Assert) pattern
with comprehensive coverage of all methods and edge cases.
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest

from boursa_vision.application.dtos import SignalDTO, TechnicalAnalysisDTO
from boursa_vision.application.services.signal_generator import SignalGenerator
from boursa_vision.application.services.technical_analyzer import TechnicalAnalyzer

# Test tolerances for floating point comparisons
FLOAT_TOLERANCE = 0.001


@pytest.fixture
def mock_technical_analyzer():
    """Create a mock TechnicalAnalyzer for testing."""
    analyzer = Mock(spec=TechnicalAnalyzer)
    analyzer.analyze_investment = AsyncMock()
    return analyzer


@pytest.fixture
def signal_generator(mock_technical_analyzer):
    """Create SignalGenerator instance with mocked dependencies."""
    return SignalGenerator(technical_analyzer=mock_technical_analyzer)


@pytest.fixture
def sample_technical_analysis():
    """Create sample technical analysis data."""
    return TechnicalAnalysisDTO(
        symbol="AAPL",
        rsi=45.0,
        macd=0.15,
        bollinger_position=0.3,
        sma_20=150.0,
        sma_50=145.0,
        volume_trend=0.25,
        support_level=140.0,
        resistance_level=160.0,
        analysis_date=datetime.now(),
    )


class TestSignalGenerator:
    """Test suite for SignalGenerator service."""

    @pytest.mark.unit
    def test_init_with_technical_analyzer(self, mock_technical_analyzer):
        """Test SignalGenerator initialization with TechnicalAnalyzer."""
        # Arrange & Act
        generator = SignalGenerator(technical_analyzer=mock_technical_analyzer)

        # Assert
        assert generator._technical_analyzer is mock_technical_analyzer

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_signal_success_buy_signal(
        self, signal_generator, mock_technical_analyzer, sample_technical_analysis
    ):
        """Test successful signal generation with BUY signal."""
        # Arrange
        symbol = "AAPL"
        # Create analysis that should trigger BUY: RSI oversold, MACD positive, SMA bullish
        analysis = TechnicalAnalysisDTO(
            symbol=symbol,
            rsi=25.0,  # Oversold -> BUY
            macd=0.15,  # Positive -> BUY
            bollinger_position=0.15,  # Near lower band -> BUY
            sma_20=150.0,
            sma_50=145.0,  # 20 > 50 -> BUY
            volume_trend=0.25,  # Strong volume
            support_level=140.0,
            resistance_level=160.0,
            analysis_date=datetime.now(),
        )
        mock_technical_analyzer.analyze_investment.return_value = analysis

        # Act
        result = await signal_generator.generate_signal(symbol)

        # Assert
        mock_technical_analyzer.analyze_investment.assert_called_once_with(symbol)
        assert isinstance(result, SignalDTO)
        assert result.symbol == symbol
        assert result.action == "BUY"
        assert result.confidence > 0.5  # Should have high confidence
        assert "RSI oversold" in result.reason
        assert isinstance(result.metadata["rsi"], (int, float))
        assert abs(float(result.metadata["rsi"]) - 25.0) < FLOAT_TOLERANCE
        assert isinstance(result.metadata["macd"], (int, float))
        assert abs(float(result.metadata["macd"]) - 0.15) < FLOAT_TOLERANCE
        assert isinstance(result.timestamp, datetime)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_signal_success_sell_signal(
        self, signal_generator, mock_technical_analyzer
    ):
        """Test successful signal generation with SELL signal."""
        # Arrange
        symbol = "TSLA"
        # Create analysis that should trigger SELL: RSI overbought, MACD negative, SMA bearish
        analysis = TechnicalAnalysisDTO(
            symbol=symbol,
            rsi=75.0,  # Overbought -> SELL
            macd=-0.15,  # Negative -> SELL
            bollinger_position=0.85,  # Near upper band -> SELL
            sma_20=140.0,
            sma_50=145.0,  # 20 < 50 -> SELL
            volume_trend=0.3,
            support_level=135.0,
            resistance_level=150.0,
            analysis_date=datetime.now(),
        )
        mock_technical_analyzer.analyze_investment.return_value = analysis

        # Act
        result = await signal_generator.generate_signal(symbol)

        # Assert
        assert result.symbol == symbol
        assert result.action == "SELL"
        assert result.confidence > 0.5
        assert "RSI overbought" in result.reason
        assert isinstance(result.metadata["rsi"], (int, float))
        assert abs(float(result.metadata["rsi"]) - 75.0) < FLOAT_TOLERANCE

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_signal_hold_signal(
        self, signal_generator, mock_technical_analyzer
    ):
        """Test signal generation with HOLD signal for neutral conditions."""
        # Arrange
        symbol = "MSFT"
        # Create neutral analysis
        analysis = TechnicalAnalysisDTO(
            symbol=symbol,
            rsi=50.0,  # Neutral
            macd=0.05,  # Weak signal
            bollinger_position=0.5,  # Middle position
            sma_20=150.0,
            sma_50=149.0,  # Very close -> converged
            volume_trend=0.1,  # Low volume
            support_level=145.0,
            resistance_level=155.0,
            analysis_date=datetime.now(),
        )
        mock_technical_analyzer.analyze_investment.return_value = analysis

        # Act
        result = await signal_generator.generate_signal(symbol)

        # Assert
        assert result.symbol == symbol
        assert result.action == "HOLD"
        assert result.confidence <= 0.5
        assert "neutral" in result.reason.lower() or "converged" in result.reason

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_signal_insufficient_data(
        self, signal_generator, mock_technical_analyzer
    ):
        """Test signal generation with insufficient data (all None values)."""
        # Arrange
        symbol = "GOOGL"
        analysis = TechnicalAnalysisDTO(
            symbol=symbol,
            rsi=None,
            macd=None,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )
        mock_technical_analyzer.analyze_investment.return_value = analysis

        # Act
        result = await signal_generator.generate_signal(symbol)

        # Assert
        assert result.symbol == symbol
        assert result.action == "HOLD"
        assert abs(result.confidence - 0.0) < FLOAT_TOLERANCE
        assert "Insufficient data for analysis" in result.reason

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_signal_error_handling(
        self, signal_generator, mock_technical_analyzer
    ):
        """Test error handling in signal generation."""
        # Arrange
        symbol = "NVDA"
        mock_technical_analyzer.analyze_investment.side_effect = ValueError(
            "Analysis failed"
        )

        # Act
        result = await signal_generator.generate_signal(symbol)

        # Assert
        assert result.symbol == symbol
        assert result.action == "HOLD"
        assert abs(result.confidence - 0.0) < FLOAT_TOLERANCE
        assert "Error generating signal" in result.reason
        assert result.metadata == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_signals_for_portfolio_success(
        self, signal_generator, mock_technical_analyzer
    ):
        """Test generating signals for multiple symbols in portfolio."""
        # Arrange
        symbols = ["AAPL", "TSLA", "MSFT"]
        analyses = [
            TechnicalAnalysisDTO(
                symbol="AAPL",
                rsi=25.0,  # BUY signal
                macd=0.15,
                bollinger_position=0.2,
                sma_20=150.0,
                sma_50=145.0,
                volume_trend=0.3,
                support_level=140.0,
                resistance_level=160.0,
                analysis_date=datetime.now(),
            ),
            TechnicalAnalysisDTO(
                symbol="TSLA",
                rsi=75.0,  # SELL signal
                macd=-0.15,
                bollinger_position=0.8,
                sma_20=140.0,
                sma_50=145.0,
                volume_trend=0.3,
                support_level=135.0,
                resistance_level=150.0,
                analysis_date=datetime.now(),
            ),
            TechnicalAnalysisDTO(
                symbol="MSFT",
                rsi=50.0,  # HOLD signal
                macd=0.05,
                bollinger_position=0.5,
                sma_20=150.0,
                sma_50=149.0,
                volume_trend=0.1,
                support_level=145.0,
                resistance_level=155.0,
                analysis_date=datetime.now(),
            ),
        ]

        # Mock analyze_investment to return different analysis for each symbol
        mock_technical_analyzer.analyze_investment.side_effect = analyses

        # Act
        results = await signal_generator.generate_signals_for_portfolio(symbols)

        # Assert
        assert len(results) == 3
        assert all(symbol in results for symbol in symbols)
        assert results["AAPL"].action == "BUY"
        assert results["TSLA"].action == "SELL"
        assert results["MSFT"].action == "HOLD"
        assert mock_technical_analyzer.analyze_investment.call_count == 3

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_signals_for_portfolio_empty_list(self, signal_generator):
        """Test generating signals for empty portfolio."""
        # Arrange
        symbols = []

        # Act
        results = await signal_generator.generate_signals_for_portfolio(symbols)

        # Assert
        assert results == {}

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_signals_for_portfolio_with_errors(
        self, signal_generator, mock_technical_analyzer
    ):
        """Test portfolio signal generation with some symbols failing."""
        # Arrange
        symbols = ["AAPL", "ERROR", "MSFT"]

        def mock_analyze_side_effect(symbol):
            if symbol == "ERROR":
                raise ValueError("Analysis failed")
            return TechnicalAnalysisDTO(
                symbol=symbol,
                rsi=50.0,
                macd=0.0,
                bollinger_position=0.5,
                sma_20=150.0,
                sma_50=150.0,
                volume_trend=0.1,
                support_level=145.0,
                resistance_level=155.0,
                analysis_date=datetime.now(),
            )

        mock_technical_analyzer.analyze_investment.side_effect = (
            mock_analyze_side_effect
        )

        # Act
        results = await signal_generator.generate_signals_for_portfolio(symbols)

        # Assert
        assert len(results) == 3  # All symbols should be included
        assert results["AAPL"].action == "HOLD"
        assert results["ERROR"].action == "HOLD"
        assert "Error generating signal" in results["ERROR"].reason
        assert results["MSFT"].action == "HOLD"

    @pytest.mark.unit
    def test_determine_signal_action_rsi_oversold(self, signal_generator):
        """Test signal determination with RSI oversold condition."""
        # Arrange
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=30.0,  # Exactly oversold threshold
            macd=None,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        action, confidence, reasoning = signal_generator._determine_signal_action(
            analysis
        )

        # Assert
        assert action == "BUY"
        assert abs(confidence - 0.7) < FLOAT_TOLERANCE
        assert "RSI oversold" in reasoning

    @pytest.mark.unit
    def test_determine_signal_action_rsi_overbought(self, signal_generator):
        """Test signal determination with RSI overbought condition."""
        # Arrange
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=70.0,  # Exactly overbought threshold
            macd=None,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        action, confidence, reasoning = signal_generator._determine_signal_action(
            analysis
        )

        # Assert
        assert action == "SELL"
        assert abs(confidence - 0.7) < FLOAT_TOLERANCE
        assert "RSI overbought" in reasoning

    @pytest.mark.unit
    def test_determine_signal_action_macd_positive(self, signal_generator):
        """Test signal determination with positive MACD."""
        # Arrange
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=None,
            macd=0.15,  # Positive and above threshold
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        action, confidence, reasoning = signal_generator._determine_signal_action(
            analysis
        )

        # Assert
        assert action == "BUY"
        assert abs(confidence - 0.6) < FLOAT_TOLERANCE
        assert "MACD positive" in reasoning

    @pytest.mark.unit
    def test_determine_signal_action_moving_averages_bullish(self, signal_generator):
        """Test signal determination with bullish moving averages."""
        # Arrange
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=None,
            macd=None,
            bollinger_position=None,
            sma_20=152.0,
            sma_50=150.0,  # 20 > 50 with > 1% difference
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        action, confidence, reasoning = signal_generator._determine_signal_action(
            analysis
        )

        # Assert
        assert action == "BUY"
        assert abs(confidence - 0.5) < FLOAT_TOLERANCE
        assert "Short MA above long MA" in reasoning

    @pytest.mark.unit
    def test_determine_signal_action_bollinger_bands_lower(self, signal_generator):
        """Test signal determination with price near lower Bollinger band."""
        # Arrange
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=None,
            macd=None,
            bollinger_position=0.15,  # Near lower band
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        action, confidence, reasoning = signal_generator._determine_signal_action(
            analysis
        )

        # Assert
        assert action == "BUY"
        assert abs(confidence - 0.6) < FLOAT_TOLERANCE
        assert "Near lower Bollinger band" in reasoning

    @pytest.mark.unit
    def test_determine_signal_action_volume_trend_enhancement(self, signal_generator):
        """Test that strong volume trend enhances signal confidence."""
        # Arrange
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=25.0,  # BUY signal
            macd=None,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=0.3,  # Strong volume trend
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        action, confidence, reasoning = signal_generator._determine_signal_action(
            analysis
        )

        # Assert
        assert action == "BUY"
        assert abs(confidence - 0.8) < FLOAT_TOLERANCE  # 0.7 + 0.1 volume boost
        assert "RSI oversold" in reasoning
        assert "Strong volume trend" in reasoning

    @pytest.mark.unit
    def test_determine_signal_action_mixed_signals_buy_majority(self, signal_generator):
        """Test signal determination with mixed signals where BUY signals dominate."""
        # Arrange
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=25.0,  # BUY
            macd=0.15,  # BUY
            bollinger_position=0.85,  # SELL
            sma_20=152.0,
            sma_50=150.0,  # BUY
            volume_trend=0.1,  # Weak volume
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        action, confidence, _ = signal_generator._determine_signal_action(analysis)

        # Assert
        assert action == "BUY"  # 3 BUY vs 1 SELL
        # Confidence should be average of BUY signals
        expected_confidence = (0.7 + 0.6 + 0.5) / 3  # RSI + MACD + MA
        assert abs(confidence - expected_confidence) < FLOAT_TOLERANCE

    @pytest.mark.unit
    def test_determine_signal_action_tied_signals_returns_hold(self, signal_generator):
        """Test signal determination when BUY and SELL signals are tied."""
        # Arrange
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=25.0,  # BUY
            macd=-0.15,  # SELL
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        action, confidence, _ = signal_generator._determine_signal_action(analysis)

        # Assert
        assert action == "HOLD"
        assert abs(confidence - 0.3) < FLOAT_TOLERANCE

    @pytest.mark.unit
    def test_create_signal_metadata_complete_analysis(
        self, signal_generator, sample_technical_analysis
    ):
        """Test metadata creation with complete analysis data."""
        # Act
        metadata = signal_generator._create_signal_metadata(sample_technical_analysis)

        # Assert
        assert abs(float(metadata["rsi"]) - 45.0) < FLOAT_TOLERANCE
        assert abs(float(metadata["macd"]) - 0.15) < FLOAT_TOLERANCE
        assert abs(float(metadata["bollinger_position"]) - 0.3) < FLOAT_TOLERANCE
        assert abs(float(metadata["volume_trend"]) - 0.25) < FLOAT_TOLERANCE
        assert "analysis_timestamp" in metadata
        assert isinstance(metadata["analysis_timestamp"], str)

    @pytest.mark.unit
    def test_create_signal_metadata_partial_analysis(self, signal_generator):
        """Test metadata creation with partial analysis data (some None values)."""
        # Arrange
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=45.0,
            macd=None,  # None value
            bollinger_position=0.3,
            sma_20=None,  # None value
            sma_50=None,  # None value
            volume_trend=None,  # None value
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        metadata = signal_generator._create_signal_metadata(analysis)

        # Assert
        assert abs(float(metadata["rsi"]) - 45.0) < FLOAT_TOLERANCE
        assert abs(float(metadata["bollinger_position"]) - 0.3) < FLOAT_TOLERANCE
        assert "macd" not in metadata  # None values should not be included
        assert "volume_trend" not in metadata
        assert "analysis_timestamp" in metadata

    @pytest.mark.unit
    def test_create_signal_metadata_empty_analysis(self, signal_generator):
        """Test metadata creation with empty analysis (all None)."""
        # Arrange
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=None,
            macd=None,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        metadata = signal_generator._create_signal_metadata(analysis)

        # Assert
        assert len(metadata) == 1  # Only timestamp should be present
        assert "analysis_timestamp" in metadata

    @pytest.mark.unit
    def test_edge_case_rsi_boundary_values(self, signal_generator):
        """Test RSI boundary values (exactly 30 and 70)."""
        # Test RSI = 30 (should be BUY)
        analysis_30 = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=30.0,
            macd=None,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )
        action, _, _ = signal_generator._determine_signal_action(analysis_30)
        assert action == "BUY"

        # Test RSI = 70 (should be SELL)
        analysis_70 = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=70.0,
            macd=None,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )
        action, _, _ = signal_generator._determine_signal_action(analysis_70)
        assert action == "SELL"

    @pytest.mark.unit
    def test_edge_case_macd_boundary_values(self, signal_generator):
        """Test MACD boundary values (exactly 0.1 and -0.1)."""
        # Test MACD = 0.1 (exact boundary should be HOLD since > 0.1 required)
        analysis_pos = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=None,
            macd=0.1,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )
        action, _, _ = signal_generator._determine_signal_action(analysis_pos)
        assert action == "HOLD"

        # Test MACD = -0.1 (exact boundary should be HOLD since < -0.1 required)
        analysis_neg = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=None,
            macd=-0.1,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )
        action, _, _ = signal_generator._determine_signal_action(analysis_neg)
        assert action == "HOLD"

        # Test MACD > 0.1 (should be BUY)
        analysis_buy = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=None,
            macd=0.15,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )
        action, _, _ = signal_generator._determine_signal_action(analysis_buy)
        assert action == "BUY"

        # Test MACD < -0.1 (should be SELL)
        analysis_sell = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=None,
            macd=-0.15,
            bollinger_position=None,
            sma_20=None,
            sma_50=None,
            volume_trend=None,
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )
        action, _, _ = signal_generator._determine_signal_action(analysis_sell)
        assert action == "SELL"

    @pytest.mark.unit
    def test_confidence_capping_at_one(self, signal_generator):
        """Test that confidence is capped at 1.0 even with volume enhancement."""
        # Arrange - Create a signal that would exceed 1.0 with volume boost
        analysis = TechnicalAnalysisDTO(
            symbol="TEST",
            rsi=25.0,  # BUY with 0.7 confidence
            macd=0.2,  # BUY with 0.6 confidence
            bollinger_position=0.1,  # BUY with 0.6 confidence
            sma_20=155.0,
            sma_50=150.0,  # BUY with 0.5 confidence
            volume_trend=0.5,  # Strong volume that would add 0.1
            support_level=None,
            resistance_level=None,
            analysis_date=datetime.now(),
        )

        # Act
        action, confidence, reasoning = signal_generator._determine_signal_action(
            analysis
        )

        # Assert
        assert action == "BUY"
        assert confidence <= 1.0  # Should be capped at 1.0
        assert "Strong volume trend" in reasoning
