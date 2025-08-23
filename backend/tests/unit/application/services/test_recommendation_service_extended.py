"""
Extended test suite for Archive-Based Recommendation Service.
Additional comprehensive tests covering internal methods and edge cases.
Continuing Priority #3 - Testing recommendation service for maximum coverage.
"""

from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest

try:
    import pandas as pd
except ImportError:
    pd = None

from boursa_vision.application.services.recommendation.recommendation_service import (
    ArchiveBasedRecommendationService,
    ArchiveDataRepository,
    ArchivedRecommendation,
    TechnicalAnalyzer,
)


class TestArchiveBasedRecommendationServiceInternal:
    """Test internal methods of ArchiveBasedRecommendationService."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ArchiveBasedRecommendationService("test_db_url")

    def test_analyze_symbol_insufficient_data(self, service):
        """Test _analyze_symbol with insufficient market data."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        service.repository = Mock()
        service.repository.get_market_data.return_value = (
            pd.DataFrame()
        )  # Empty DataFrame
        service.repository.get_symbol_info.return_value = {"name": "Test Stock"}

        # Act
        result = service._analyze_symbol("TEST")

        # Assert
        assert result is None

    def test_analyze_symbol_minimal_data(self, service):
        """Test _analyze_symbol with minimal valid data."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        service.repository = Mock()

        # Create minimal valid DataFrame (5 rows)
        test_data = pd.DataFrame(
            {
                "close": [100.0, 101.0, 102.0, 101.5, 103.0],
                "volume": [1000, 1100, 1050, 1200, 1150],
            }
        )

        service.repository.get_market_data.return_value = test_data
        service.repository.get_symbol_info.return_value = {
            "name": "Test Stock",
            "symbol": "TEST",
            "instrument_type": "stock",
            "currency": "USD",
        }

        # Act
        result = service._analyze_symbol("TEST")

        # Assert
        assert result is not None
        assert isinstance(result, ArchivedRecommendation)
        assert result.symbol == "TEST"
        assert result.name == "Test Stock"
        assert result.recommendation in ["BUY", "HOLD", "SELL"]

    def test_score_rsi_oversold_conditions(self, service):
        """Test RSI scoring for oversold conditions."""
        # Act
        score = service._score_rsi(25.0)  # Oversold

        # Assert
        assert score == 85

    def test_score_rsi_overbought_conditions(self, service):
        """Test RSI scoring for overbought conditions."""
        # Act
        score = service._score_rsi(75.0)  # Overbought

        # Assert
        assert score == 25

    def test_score_rsi_neutral_conditions(self, service):
        """Test RSI scoring for neutral conditions."""
        # Act
        score = service._score_rsi(55.0)  # Neutral

        # Assert
        assert score == 65

    def test_score_moving_averages_above_all(self, service):
        """Test moving averages scoring when price is above all MAs."""
        # Arrange
        current_price = 110.0
        mas = {"ma_5": 105.0, "ma_10": 100.0, "ma_20": 95.0, "ma_50": 90.0}

        # Act
        score = service._score_moving_averages(current_price, mas)

        # Assert
        assert abs(score - 70.0) < 0.01  # 30 + (4/4 * 40)

    def test_score_moving_averages_below_all(self, service):
        """Test moving averages scoring when price is below all MAs."""
        # Arrange
        current_price = 85.0
        mas = {"ma_5": 105.0, "ma_10": 100.0, "ma_20": 95.0, "ma_50": 90.0}

        # Act
        score = service._score_moving_averages(current_price, mas)

        # Assert
        assert abs(score - 30.0) < 0.01  # 30 + (0/4 * 40)

    def test_score_moving_averages_empty(self, service):
        """Test moving averages scoring with empty MAs."""
        # Arrange
        current_price = 100.0
        mas = {}

        # Act
        score = service._score_moving_averages(current_price, mas)

        # Assert
        assert score == 50  # Default score when no MAs

    def test_calculate_price_changes_full_data(self, service):
        """Test price changes calculation with full data."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        # Create prices series with 35 data points
        prices = pd.Series([100 + i * 0.5 for i in range(35)])

        # Act
        changes = service._calculate_price_changes(prices)

        # Assert
        assert "1d" in changes
        assert "7d" in changes
        assert "30d" in changes
        assert all(isinstance(change, float) for change in changes.values())

    def test_calculate_price_changes_insufficient_data(self, service):
        """Test price changes calculation with insufficient data."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        prices = pd.Series([100.0, 101.0])  # Only 2 data points

        # Act
        changes = service._calculate_price_changes(prices)

        # Assert
        assert abs(changes["1d"]) > 0.01  # Should calculate 1d change
        assert abs(changes["7d"]) < 0.01  # Should return 0 for insufficient data
        assert abs(changes["30d"]) < 0.01  # Should return 0 for insufficient data

    def test_score_momentum_strong_positive(self, service):
        """Test momentum scoring for strong positive momentum."""
        # Arrange
        price_changes = {"1d": 15.0, "7d": 10.0, "30d": 8.0}

        # Act
        score = service._score_momentum(price_changes)

        # Assert
        assert score == 90  # Should get maximum score for strong positive momentum

    def test_score_momentum_strong_negative(self, service):
        """Test momentum scoring for strong negative momentum."""
        # Arrange
        price_changes = {"1d": -8.0, "7d": -6.0, "30d": -10.0}

        # Act
        score = service._score_momentum(price_changes)

        # Assert
        assert score == 20  # Should get low score for strong negative momentum

    def test_score_momentum_neutral(self, service):
        """Test momentum scoring for neutral momentum."""
        # Arrange
        price_changes = {"1d": 1.0, "7d": 0.5, "30d": -0.5}

        # Act
        score = service._score_momentum(price_changes)

        # Assert
        assert score == 60  # Should get neutral score

    def test_analyze_volume_increasing_trend(self, service):
        """Test volume analysis for increasing trend."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        # Create DataFrame with increasing volume trend
        volumes = [1000] * 10 + [1300] * 5  # Recent volume 30% higher
        df = pd.DataFrame({"volume": volumes})

        # Act
        result = service._analyze_volume(df)

        # Assert
        assert result["trend"] == "INCREASING"
        assert result["avg_volume"] > 0
        assert result["recent_vs_avg"] > 1.0

    def test_analyze_volume_decreasing_trend(self, service):
        """Test volume analysis for decreasing trend."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        # Create DataFrame with decreasing volume trend
        volumes = [1000] * 10 + [700] * 5  # Recent volume 30% lower
        df = pd.DataFrame({"volume": volumes})

        # Act
        result = service._analyze_volume(df)

        # Assert
        assert result["trend"] == "DECREASING"
        assert result["avg_volume"] > 0
        assert result["recent_vs_avg"] < 1.0

    def test_analyze_volume_stable_trend(self, service):
        """Test volume analysis for stable trend."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        # Create DataFrame with stable volume
        volumes = [1000] * 15  # Consistent volume
        df = pd.DataFrame({"volume": volumes})

        # Act
        result = service._analyze_volume(df)

        # Assert
        assert result["trend"] == "STABLE"
        assert abs(result["avg_volume"] - 1000.0) < 0.01
        assert abs(result["recent_vs_avg"] - 1.0) < 0.01

    def test_analyze_volume_small_dataset(self, service):
        """Test volume analysis with small dataset."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        # Create DataFrame with less than 10 data points
        volumes = [1000, 1100, 1050]
        df = pd.DataFrame({"volume": volumes})

        # Act
        result = service._analyze_volume(df)

        # Assert
        assert result["trend"] in ["INCREASING", "DECREASING", "STABLE"]
        assert result["avg_volume"] > 0

    def test_score_volume_increasing(self, service):
        """Test volume scoring for increasing volume."""
        # Arrange
        volume_analysis = {
            "trend": "INCREASING",
            "avg_volume": 1000000,
            "recent_vs_avg": 1.3,
        }

        # Act
        score = service._score_volume(volume_analysis)

        # Assert
        assert score == 75

    def test_score_volume_stable(self, service):
        """Test volume scoring for stable volume."""
        # Arrange
        volume_analysis = {
            "trend": "STABLE",
            "avg_volume": 1000000,
            "recent_vs_avg": 1.0,
        }

        # Act
        score = service._score_volume(volume_analysis)

        # Assert
        assert score == 60

    def test_score_volume_decreasing(self, service):
        """Test volume scoring for decreasing volume."""
        # Arrange
        volume_analysis = {
            "trend": "DECREASING",
            "avg_volume": 1000000,
            "recent_vs_avg": 0.7,
        }

        # Act
        score = service._score_volume(volume_analysis)

        # Assert
        assert score == 45

    def test_assess_risk_low(self, service):
        """Test risk assessment for low risk."""
        # Arrange
        volatility = 3.0
        price_changes = {"7d": 1.0}

        # Act
        risk_level = service._assess_risk(volatility, price_changes)

        # Assert
        assert risk_level == "LOW"

    def test_assess_risk_moderate(self, service):
        """Test risk assessment for moderate risk."""
        # Arrange
        volatility = 8.0
        price_changes = {"7d": 3.0}

        # Act
        risk_level = service._assess_risk(volatility, price_changes)

        # Assert
        assert risk_level == "MODERATE"

    def test_assess_risk_high(self, service):
        """Test risk assessment for high risk."""
        # Arrange
        volatility = 20.0
        price_changes = {"7d": 10.0}

        # Act
        risk_level = service._assess_risk(volatility, price_changes)

        # Assert
        assert risk_level == "HIGH"

    def test_calculate_confidence_high_data_quality(self, service):
        """Test confidence calculation with high data quality."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        # Create DataFrame with 50+ data points
        df = pd.DataFrame({"close": [100 + i for i in range(60)]})
        rsi = 55.0  # Normal RSI
        volatility = 10.0  # Normal volatility

        # Act
        confidence = service._calculate_confidence(df, rsi, volatility)

        # Assert
        assert confidence > 0.9  # Should have high confidence

    def test_calculate_confidence_low_data_quality(self, service):
        """Test confidence calculation with low data quality."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        # Create DataFrame with few data points
        df = pd.DataFrame({"close": [100, 101, 102]})
        rsi = 95.0  # Extreme RSI
        volatility = 35.0  # High volatility

        # Act
        confidence = service._calculate_confidence(df, rsi, volatility)

        # Assert
        assert confidence < 0.5  # Should have low confidence

    def test_determine_recommendation_strong_buy(self, service):
        """Test recommendation determination for strong buy conditions."""
        # Act
        recommendation = service._determine_recommendation(80.0, 70.0, 75.0)

        # Assert
        assert recommendation == "BUY"

    def test_determine_recommendation_hold(self, service):
        """Test recommendation determination for hold conditions."""
        # Act
        recommendation = service._determine_recommendation(60.0, 55.0, 65.0)

        # Assert
        assert recommendation == "HOLD"

    def test_determine_recommendation_sell(self, service):
        """Test recommendation determination for sell conditions."""
        # Act
        recommendation = service._determine_recommendation(40.0, 35.0, 45.0)

        # Assert
        assert recommendation == "SELL"

    def test_generate_insights_oversold_conditions(self, service):
        """Test insights generation for oversold conditions."""
        # Arrange
        rsi = 25.0
        mas = {"ma_5": 100.0, "ma_10": 95.0}
        price_changes = {"7d": 8.0}
        volume_analysis = {"trend": "INCREASING"}
        current_price = 105.0

        # Act
        strengths, _, insights = service._generate_insights(
            rsi, mas, price_changes, volume_analysis, current_price
        )

        # Assert
        assert len(strengths) > 0
        assert any("oversold" in strength.lower() for strength in strengths)
        assert any("positive momentum" in strength.lower() for strength in strengths)
        assert len(insights) > 0

    def test_generate_insights_overbought_conditions(self, service):
        """Test insights generation for overbought conditions."""
        # Arrange
        rsi = 80.0
        mas = {"ma_5": 100.0, "ma_10": 95.0}
        price_changes = {"7d": -8.0}
        volume_analysis = {"trend": "DECREASING"}
        current_price = 90.0  # Below most MAs

        # Act
        _, weaknesses, insights = service._generate_insights(
            rsi, mas, price_changes, volume_analysis, current_price
        )

        # Assert
        assert len(weaknesses) > 0
        assert any("overbought" in weakness.lower() for weakness in weaknesses)
        assert any("negative momentum" in weakness.lower() for weakness in weaknesses)
        assert len(insights) > 0

    def test_generate_insights_mixed_conditions(self, service):
        """Test insights generation for mixed market conditions."""
        # Arrange
        rsi = 55.0  # Neutral
        mas = {"ma_5": 100.0, "ma_10": 95.0, "ma_20": 90.0, "ma_50": 85.0}
        price_changes = {"7d": 2.0, "30d": 5.0}
        volume_analysis = {"trend": "STABLE"}
        current_price = 97.0  # Above some MAs, below others

        # Act
        strengths, weaknesses, insights = service._generate_insights(
            rsi, mas, price_changes, volume_analysis, current_price
        )

        # Assert
        assert isinstance(strengths, list)
        assert isinstance(weaknesses, list)
        assert isinstance(insights, list)
        assert len(insights) >= 2  # Should have trend and volume insights


class TestRecommendationServiceMainFunction:
    """Test the main function for completeness."""

    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables."""
        with patch.dict(
            "os.environ", {"DATABASE_URL": "postgresql://test:test@localhost/test"}
        ):
            yield

    def test_main_function_execution(self, mock_env_vars):
        """Test main function can execute without errors."""
        # Arrange
        with patch(
            "boursa_vision.application.services.recommendation.recommendation_service.ArchiveBasedRecommendationService"
        ) as mock_service_class:
            mock_service = Mock()
            mock_service.get_recommendations.return_value = [
                Mock(
                    symbol="TEST",
                    recommendation="BUY",
                    overall_score=85.0,
                    confidence=0.9,
                    current_price=100.0,
                    risk_level="LOW",
                    strengths=["Strong momentum", "Good volume"],
                )
            ]
            mock_service_class.return_value = mock_service

            # Import and call main function
            from boursa_vision.application.services.recommendation.recommendation_service import (
                main,
            )

            # Act & Assert - Should not raise any exceptions
            main()  # Let any exceptions (including SystemExit) propagate normally


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""

    @pytest.fixture
    def service(self):
        """Create service instance for testing."""
        return ArchiveBasedRecommendationService("test_db_url")

    def test_score_rsi_boundary_values(self, service):
        """Test RSI scoring at boundary values."""
        # Test exact boundary values
        assert service._score_rsi(30.0) == 85  # Exactly at oversold threshold
        assert service._score_rsi(70.0) == 45  # Exactly at overbought threshold
        assert service._score_rsi(0.0) == 85  # Minimum RSI
        assert service._score_rsi(100.0) == 25  # Maximum RSI

    def test_score_momentum_edge_cases(self, service):
        """Test momentum scoring with edge case values."""
        # Test with missing price change data
        empty_changes = {}
        score = service._score_momentum(empty_changes)
        assert score == 50  # Should handle missing data gracefully

        # Test with very large positive change
        large_positive = {"1d": 50.0, "7d": 30.0, "30d": 20.0}
        score = service._score_momentum(large_positive)
        assert score == 90

        # Test with very large negative change
        large_negative = {"1d": -50.0, "7d": -30.0, "30d": -20.0}
        score = service._score_momentum(large_negative)
        assert score == 20

    def test_analyze_volume_zero_volume(self, service):
        """Test volume analysis with zero volume data."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        df = pd.DataFrame({"volume": [0, 0, 0, 0, 0]})

        # Act
        result = service._analyze_volume(df)

        # Assert
        assert result["avg_volume"] == 0
        assert result["trend"] in ["INCREASING", "DECREASING", "STABLE"]
        assert (
            abs(result["recent_vs_avg"] - 1.0) < 0.01
        )  # Should handle division by zero

    def test_calculate_confidence_boundary_conditions(self, service):
        """Test confidence calculation at boundary conditions."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")

        # Test maximum confidence scenario
        large_df = pd.DataFrame({"close": [100] * 100})  # 100 data points
        confidence = service._calculate_confidence(large_df, 50.0, 10.0)
        assert confidence <= 1.0  # Should not exceed 1.0

        # Test minimum confidence scenario
        tiny_df = pd.DataFrame({"close": [100]})  # 1 data point
        confidence = service._calculate_confidence(tiny_df, 5.0, 50.0)
        assert confidence >= 0.0  # Should not go below 0.0


@pytest.mark.integration
class TestRecommendationServiceIntegration:
    """Integration tests for the recommendation service."""

    def test_full_analysis_workflow(self):
        """Test complete analysis workflow with mocked data."""
        # This test would verify the full workflow from data retrieval to recommendation
        # In a real scenario, this would use a test database with known data

        service = ArchiveBasedRecommendationService("test_db_url")

        # Mock the repository methods
        service.repository = Mock()
        service.repository.get_available_symbols.return_value = ["TEST"]

        if pd:
            # Create realistic market data
            test_data = pd.DataFrame(
                {
                    "close": [100.0, 101.0, 102.0, 101.5, 103.0, 104.0, 103.5, 105.0],
                    "volume": [
                        1000000,
                        1100000,
                        1050000,
                        1200000,
                        1150000,
                        1300000,
                        1250000,
                        1400000,
                    ],
                }
            )
            service.repository.get_market_data.return_value = test_data
        else:
            # Skip if pandas not available
            pytest.skip("pandas not available")

        service.repository.get_symbol_info.return_value = {
            "symbol": "TEST",
            "name": "Test Stock Inc.",
            "instrument_type": "stock",
            "currency": "USD",
        }

        # Act
        recommendations = service.get_recommendations(
            max_recommendations=1, min_score=0.0
        )

        # Assert
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.symbol == "TEST"
        assert rec.name == "Test Stock Inc."
        assert rec.recommendation in ["BUY", "HOLD", "SELL"]
        assert 0 <= rec.overall_score <= 100
        assert 0 <= rec.confidence <= 1
        assert rec.risk_level in ["LOW", "MODERATE", "HIGH"]
