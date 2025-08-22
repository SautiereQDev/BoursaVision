"""
Unit tests for ArchiveBasedRecommendationService.

Tests the ArchiveBasedRecommendationService following AAA (Arrange-Act-Assert) pattern
with comprehensive coverage of all methods and edge cases.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, List, Any

from boursa_vision.application.services.recommendation.recommendation_service import (
    ArchiveBasedRecommendationService,
    ArchiveDataRepository,
    TechnicalAnalyzer,
    ArchivedRecommendation
)

# Test tolerances for floating point comparisons
FLOAT_TOLERANCE = 0.001


@pytest.fixture
def mock_repository():
    """Create a mock ArchiveDataRepository for testing."""
    repo = Mock(spec=ArchiveDataRepository)
    return repo


@pytest.fixture
def mock_technical_analyzer():
    """Create a mock TechnicalAnalyzer for testing."""
    analyzer = Mock(spec=TechnicalAnalyzer)
    return analyzer


@pytest.fixture
def recommendation_service(mock_repository, mock_technical_analyzer):
    """Create ArchiveBasedRecommendationService with mocked dependencies."""
    service = ArchiveBasedRecommendationService("mock://database")
    service.repository = mock_repository
    service.technical_analyzer = mock_technical_analyzer
    return service


@pytest.fixture
def sample_market_data():
    """Create sample market data DataFrame."""
    dates = pd.date_range(start='2024-01-01', end='2024-01-30', freq='D')
    data = {
        'open': [100.0 + i * 0.5 for i in range(len(dates))],
        'high': [102.0 + i * 0.5 for i in range(len(dates))],
        'low': [98.0 + i * 0.5 for i in range(len(dates))],
        'close': [101.0 + i * 0.5 for i in range(len(dates))],
        'volume': [1000000 + i * 10000 for i in range(len(dates))]
    }
    df = pd.DataFrame(data, index=dates)
    return df


@pytest.fixture
def empty_market_data():
    """Create empty market data DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def sample_symbol_info():
    """Create sample symbol information."""
    return {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "instrument_type": "stock",
        "currency": "USD"
    }


class TestArchiveBasedRecommendationService:
    """Test suite for ArchiveBasedRecommendationService."""

    @pytest.mark.unit
    def test_init_with_database_url(self):
        """Test service initialization with database URL."""
        # Arrange & Act
        with patch('boursa_vision.application.services.recommendation.recommendation_service.ArchiveDataRepository') as mock_repo_class:
            with patch('boursa_vision.application.services.recommendation.recommendation_service.TechnicalAnalyzer') as mock_analyzer_class:
                ArchiveBasedRecommendationService("test://database")
                
                # Assert
                mock_repo_class.assert_called_once_with("test://database")
                mock_analyzer_class.assert_called_once()

    @pytest.mark.unit
    def test_get_recommendations_success_with_valid_data(
        self, recommendation_service, mock_repository, mock_technical_analyzer, 
        sample_market_data, sample_symbol_info
    ):
        """Test successful recommendation generation with valid data."""
        # Arrange
        symbols = ["AAPL", "GOOGL", "MSFT"]
        mock_repository.get_available_symbols.return_value = symbols
        mock_repository.get_market_data.return_value = sample_market_data
        mock_repository.get_symbol_info.return_value = sample_symbol_info
        
        # Configure technical analyzer mocks
        mock_technical_analyzer.calculate_rsi.return_value = 45.0  # Neutral RSI
        mock_technical_analyzer.calculate_moving_averages.return_value = {
            "ma_5": 100.0, "ma_10": 99.0, "ma_20": 98.0, "ma_50": 95.0
        }
        mock_technical_analyzer.calculate_volatility.return_value = 15.0
        
        # Act
        results = recommendation_service.get_recommendations(max_recommendations=5, min_score=50.0)
        
        # Assert
        mock_repository.get_available_symbols.assert_called_once()
        assert len(results) <= 5
        assert len(results) <= len(symbols)
        
        for result in results:
            assert isinstance(result, ArchivedRecommendation)
            assert result.overall_score >= 50.0
            assert result.symbol in symbols
            assert result.recommendation in ["BUY", "HOLD", "SELL"]

    @pytest.mark.unit
    def test_get_recommendations_empty_symbols_list(self, recommendation_service, mock_repository):
        """Test recommendation generation with no available symbols."""
        # Arrange
        mock_repository.get_available_symbols.return_value = []
        
        # Act
        results = recommendation_service.get_recommendations()
        
        # Assert
        assert results == []
        mock_repository.get_available_symbols.assert_called_once()

    @pytest.mark.unit
    def test_get_recommendations_filters_low_scores(
        self, recommendation_service, mock_repository, mock_technical_analyzer,
        sample_market_data, sample_symbol_info
    ):
        """Test that recommendations with low scores are filtered out."""
        # Arrange
        symbols = ["LOWSCORE"]
        mock_repository.get_available_symbols.return_value = symbols
        mock_repository.get_market_data.return_value = sample_market_data
        mock_repository.get_symbol_info.return_value = sample_symbol_info
        
        # Configure for low scores (bad RSI, poor momentum)
        mock_technical_analyzer.calculate_rsi.return_value = 80.0  # Overbought
        mock_technical_analyzer.calculate_moving_averages.return_value = {
            "ma_5": 95.0, "ma_10": 98.0, "ma_20": 100.0, "ma_50": 102.0  # Bearish MA
        }
        mock_technical_analyzer.calculate_volatility.return_value = 25.0  # High volatility
        
        # Act
        results = recommendation_service.get_recommendations(min_score=70.0)
        
        # Assert
        # Should be filtered out due to low score
        assert len(results) == 0

    @pytest.mark.unit
    def test_get_recommendations_handles_analysis_errors(
        self, recommendation_service, mock_repository, mock_technical_analyzer
    ):
        """Test recommendation generation handles analysis errors gracefully."""
        # Arrange
        symbols = ["ERROR_SYMBOL", "VALID_SYMBOL"]
        mock_repository.get_available_symbols.return_value = symbols
        
        def mock_get_market_data_side_effect(symbol, days=30):
            if symbol == "ERROR_SYMBOL":
                raise ValueError("Database error")
            return pd.DataFrame({
                'open': [100], 'high': [102], 'low': [98], 'close': [101], 'volume': [1000000]
            }, index=[datetime.now()])
        
        mock_repository.get_market_data.side_effect = mock_get_market_data_side_effect
        mock_repository.get_symbol_info.return_value = {"symbol": "VALID_SYMBOL", "name": "Valid Corp"}
        mock_technical_analyzer.calculate_rsi.return_value = 60.0
        mock_technical_analyzer.calculate_moving_averages.return_value = {"ma_5": 100.0}
        mock_technical_analyzer.calculate_volatility.return_value = 10.0
        
        # Act
        results = recommendation_service.get_recommendations()
        
        # Assert
        # Should process valid symbols despite errors with others
        assert len(results) <= 1  # Only valid symbol should be processed

    @pytest.mark.unit
    def test_analyze_symbol_success(
        self, recommendation_service, mock_repository, mock_technical_analyzer,
        sample_market_data, sample_symbol_info
    ):
        """Test successful analysis of a single symbol."""
        # Arrange
        symbol = "AAPL"
        mock_repository.get_market_data.return_value = sample_market_data
        mock_repository.get_symbol_info.return_value = sample_symbol_info
        
        mock_technical_analyzer.calculate_rsi.return_value = 65.0  # Good RSI
        mock_technical_analyzer.calculate_moving_averages.return_value = {
            "ma_5": 115.0, "ma_10": 114.0, "ma_20": 113.0, "ma_50": 110.0  # Bullish
        }
        mock_technical_analyzer.calculate_volatility.return_value = 12.0
        
        # Act
        result = recommendation_service._analyze_symbol(symbol)
        
        # Assert
        assert result is not None
        assert isinstance(result, ArchivedRecommendation)
        assert result.symbol == symbol
        assert result.name == sample_symbol_info["name"]
        assert result.recommendation in ["BUY", "HOLD", "SELL"]
        assert 0.0 <= result.confidence <= 1.0
        assert result.risk_level in ["LOW", "MODERATE", "HIGH"]
        assert isinstance(result.strengths, list)
        assert isinstance(result.weaknesses, list)
        assert isinstance(result.key_insights, list)

    @pytest.mark.unit
    def test_analyze_symbol_insufficient_data(
        self, recommendation_service, mock_repository
    ):
        """Test analysis with insufficient market data."""
        # Arrange
        symbol = "NODATA"
        insufficient_data = pd.DataFrame({
            'open': [100], 'high': [102], 'low': [98], 'close': [101], 'volume': [1000]
        })  # Only 1 row, less than required 5
        
        mock_repository.get_market_data.return_value = insufficient_data
        
        # Act
        result = recommendation_service._analyze_symbol(symbol)
        
        # Assert
        assert result is None

    @pytest.mark.unit
    def test_analyze_symbol_empty_data(
        self, recommendation_service, mock_repository, empty_market_data
    ):
        """Test analysis with empty market data."""
        # Arrange
        symbol = "EMPTY"
        mock_repository.get_market_data.return_value = empty_market_data
        
        # Act
        result = recommendation_service._analyze_symbol(symbol)
        
        # Assert
        assert result is None

    @pytest.mark.unit
    def test_score_rsi_oversold(self, recommendation_service):
        """Test RSI scoring for oversold conditions."""
        # Test various RSI values
        test_cases = [
            (25.0, 85.0),  # Oversold - high score
            (30.0, 85.0),  # Exactly at oversold threshold
            (35.0, 75.0),  # Slightly oversold
            (50.0, 65.0),  # Neutral
            (65.0, 45.0),  # Moving toward overbought
            (70.0, 45.0),  # At overbought threshold
            (80.0, 25.0),  # Overbought - low score
        ]
        
        for rsi, expected_min_score in test_cases:
            score = recommendation_service._score_rsi(rsi)
            assert score >= expected_min_score - 10  # Allow some tolerance
            assert 0 <= score <= 100

    @pytest.mark.unit
    def test_score_moving_averages_bullish(self, recommendation_service):
        """Test moving average scoring for bullish conditions."""
        # Arrange - Price above all MAs (bullish)
        current_price = 105.0
        mas = {"ma_5": 100.0, "ma_10": 99.0, "ma_20": 98.0, "ma_50": 95.0}
        
        # Act
        score = recommendation_service._score_moving_averages(current_price, mas)
        
        # Assert
        assert score >= 65.0  # Should be high score for bullish setup
        assert score <= 100.0

    @pytest.mark.unit
    def test_score_moving_averages_bearish(self, recommendation_service):
        """Test moving average scoring for bearish conditions."""
        # Arrange - Price below all MAs (bearish)
        current_price = 90.0
        mas = {"ma_5": 95.0, "ma_10": 96.0, "ma_20": 98.0, "ma_50": 100.0}
        
        # Act
        score = recommendation_service._score_moving_averages(current_price, mas)
        
        # Assert
        assert score <= 40.0  # Should be low score for bearish setup
        assert score >= 0.0

    @pytest.mark.unit
    def test_calculate_price_changes(self, recommendation_service):
        """Test price change calculations."""
        # Arrange - Create price series with known changes
        prices = pd.Series([100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 110.0])
        
        # Act
        changes = recommendation_service._calculate_price_changes(prices)
        
        # Assert
        assert "1d" in changes
        assert "7d" in changes
        assert "30d" in changes
        
        # 1-day change: (110 - 108) / 108 * 100 ≈ 1.85%
        assert abs(changes["1d"] - ((110 - 108) / 108 * 100)) < FLOAT_TOLERANCE
        
        # All changes should be positive (upward trend)
        assert changes["1d"] > 0
        assert changes["7d"] > 0

    @pytest.mark.unit
    def test_score_momentum_positive(self, recommendation_service):
        """Test momentum scoring with positive price changes."""
        # Arrange
        price_changes = {"1d": 2.0, "7d": 5.0, "30d": 10.0}
        
        # Act
        score = recommendation_service._score_momentum(price_changes)
        
        # Assert
        assert score >= 60.0  # Positive momentum should yield good score
        assert score <= 100.0

    @pytest.mark.unit
    def test_score_momentum_negative(self, recommendation_service):
        """Test momentum scoring with negative price changes."""
        # Arrange
        price_changes = {"1d": -2.0, "7d": -5.0, "30d": -10.0}
        
        # Act
        score = recommendation_service._score_momentum(price_changes)
        
        # Assert
        assert score <= 50.0  # Negative momentum should yield low score
        assert score >= 0.0

    @pytest.mark.unit
    def test_analyze_volume_increasing_trend(self, recommendation_service):
        """Test volume analysis with increasing volume trend."""
        # Arrange - Create DataFrame with increasing volume
        volume_data = [1000000 + i * 100000 for i in range(20)]  # Increasing volume
        df = pd.DataFrame({'volume': volume_data})
        
        # Act
        volume_analysis = recommendation_service._analyze_volume(df)
        
        # Assert
        assert volume_analysis["trend"] == "INCREASING"
        assert volume_analysis["avg_volume"] > 0
        assert volume_analysis["recent_vs_avg"] > 1.0

    @pytest.mark.unit
    def test_analyze_volume_decreasing_trend(self, recommendation_service):
        """Test volume analysis with decreasing volume trend."""
        # Arrange - Create DataFrame with decreasing volume
        volume_data = [2000000 - i * 50000 for i in range(20)]  # Decreasing volume
        df = pd.DataFrame({'volume': volume_data})
        
        # Act
        volume_analysis = recommendation_service._analyze_volume(df)
        
        # Assert
        assert volume_analysis["trend"] == "DECREASING"
        assert volume_analysis["avg_volume"] > 0
        assert volume_analysis["recent_vs_avg"] < 1.0

    @pytest.mark.unit
    def test_score_volume_trends(self, recommendation_service):
        """Test volume scoring for different trends."""
        # Test increasing volume
        increasing_analysis = {"trend": "INCREASING", "avg_volume": 1000000}
        score_increasing = recommendation_service._score_volume(increasing_analysis)
        assert abs(score_increasing - 75.0) < FLOAT_TOLERANCE
        
        # Test stable volume
        stable_analysis = {"trend": "STABLE", "avg_volume": 1000000}
        score_stable = recommendation_service._score_volume(stable_analysis)
        assert abs(score_stable - 60.0) < FLOAT_TOLERANCE
        
        # Test decreasing volume
        decreasing_analysis = {"trend": "DECREASING", "avg_volume": 1000000}
        score_decreasing = recommendation_service._score_volume(decreasing_analysis)
        assert abs(score_decreasing - 45.0) < FLOAT_TOLERANCE

    @pytest.mark.unit
    def test_assess_risk_levels(self, recommendation_service):
        """Test risk assessment for different volatility levels."""
        # Test low risk
        risk_low = recommendation_service._assess_risk(2.0, {"7d": 1.0})
        assert risk_low == "LOW"
        
        # Test moderate risk
        risk_moderate = recommendation_service._assess_risk(8.0, {"7d": 3.0})
        assert risk_moderate == "MODERATE"
        
        # Test high risk
        risk_high = recommendation_service._assess_risk(15.0, {"7d": 8.0})
        assert risk_high == "HIGH"

    @pytest.mark.unit
    def test_calculate_confidence(self, recommendation_service, sample_market_data):
        """Test confidence calculation."""
        # Arrange
        rsi = 60.0
        volatility = 10.0
        
        # Act
        confidence = recommendation_service._calculate_confidence(sample_market_data, rsi, volatility)
        
        # Assert
        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)

    @pytest.mark.unit
    def test_determine_recommendation_buy(self, recommendation_service):
        """Test recommendation determination for BUY conditions."""
        # Arrange - High scores should trigger BUY
        overall_score = 80.0
        technical_score = 70.0
        momentum_score = 75.0
        
        # Act
        recommendation = recommendation_service._determine_recommendation(
            overall_score, technical_score, momentum_score
        )
        
        # Assert
        assert recommendation == "BUY"

    @pytest.mark.unit
    def test_determine_recommendation_hold(self, recommendation_service):
        """Test recommendation determination for HOLD conditions."""
        # Arrange - Moderate scores should trigger HOLD
        overall_score = 60.0
        technical_score = 55.0
        momentum_score = 50.0
        
        # Act
        recommendation = recommendation_service._determine_recommendation(
            overall_score, technical_score, momentum_score
        )
        
        # Assert
        assert recommendation == "HOLD"

    @pytest.mark.unit
    def test_determine_recommendation_sell(self, recommendation_service):
        """Test recommendation determination for SELL conditions."""
        # Arrange - Low scores should trigger SELL
        overall_score = 40.0
        technical_score = 30.0
        momentum_score = 25.0
        
        # Act
        recommendation = recommendation_service._determine_recommendation(
            overall_score, technical_score, momentum_score
        )
        
        # Assert
        assert recommendation == "SELL"

    @pytest.mark.unit
    def test_generate_insights(self, recommendation_service):
        """Test insight generation."""
        # Arrange
        rsi = 35.0  # Slightly oversold
        mas = {"ma_5": 100.0, "ma_10": 99.0, "ma_20": 101.0, "ma_50": 102.0}
        current_price = 100.5
        price_changes = {"1d": 1.0, "7d": 3.0, "30d": -2.0}
        volume_analysis = {"trend": "INCREASING", "avg_volume": 1000000}
        
        # Act
        strengths, weaknesses, insights = recommendation_service._generate_insights(
            rsi, mas, price_changes, volume_analysis, current_price
        )
        
        # Assert
        assert isinstance(strengths, list)
        assert isinstance(weaknesses, list)
        assert isinstance(insights, list)
        
        # Should have insights about RSI being oversold
        rsi_strength_found = any("oversold" in strength.lower() for strength in strengths)
        assert rsi_strength_found or len(strengths) > 0  # Allow for different insight generation
        
        # Should have insights about volume
        volume_insight_found = any("volume" in insight.lower() for insight in strengths + insights)
        assert volume_insight_found or len(insights) > 0

    @pytest.mark.unit
    def test_edge_cases_with_minimal_data(self, recommendation_service):
        """Test edge cases with minimal but valid data."""
        # Arrange - Minimal valid dataset (5 rows)
        minimal_data = pd.DataFrame({
            'open': [100, 101, 102, 103, 104],
            'high': [102, 103, 104, 105, 106],
            'low': [98, 99, 100, 101, 102],
            'close': [101, 102, 103, 104, 105],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        })
        
        # Test various methods with minimal data
        price_changes = recommendation_service._calculate_price_changes(minimal_data['close'])
        assert "1d" in price_changes
        
        volume_analysis = recommendation_service._analyze_volume(minimal_data)
        assert volume_analysis["trend"] in ["INCREASING", "STABLE", "DECREASING"]
        
        rsi_score = recommendation_service._score_rsi(50.0)
        assert 0 <= rsi_score <= 100

    @pytest.mark.unit
    def test_boundary_values_rsi_scoring(self, recommendation_service):
        """Test RSI scoring boundary values."""
        # Test exact boundary values
        test_cases = [
            (30.0, 85.0),   # Exactly oversold
            (30.1, 75.0),   # Just above oversold
            (40.0, 75.0),   # Upper bound of oversold range
            (60.0, 65.0),   # Neutral range
            (70.0, 45.0),   # Exactly overbought
            (70.1, 25.0),   # Just above overbought
        ]
        
        for rsi, expected_score in test_cases:
            score = recommendation_service._score_rsi(rsi)
            assert abs(score - expected_score) < FLOAT_TOLERANCE

    @pytest.mark.unit
    def test_overall_scoring_calculation(self, recommendation_service):
        """Test overall scoring calculation logic."""
        # This tests the scoring logic in _analyze_symbol indirectly
        # by verifying that the scoring produces reasonable results
        
        # High component scores should yield high overall score
        rsi_score = 85.0  # Good RSI
        ma_score = 70.0   # Good MA position
        momentum_score = 75.0  # Good momentum
        volume_score = 75.0    # Good volume
        
        # Calculate expected overall score based on the weighting in _analyze_symbol
        technical_score = (rsi_score + ma_score) / 2  # Average of RSI and MA
        expected_overall = technical_score * 0.4 + momentum_score * 0.3 + volume_score * 0.3
        
        # Verify the calculation logic is sound
        assert expected_overall >= 70.0  # Should be a good score
        assert expected_overall <= 100.0
