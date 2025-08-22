"""
Test suite for Archive-Based Recommendation Service.
Comprehensive testing of recommendation engine using archived market data.
Priority #3 - Testing 247-line recommendation service for maximum coverage impact.
"""

import datetime
import pytest
from decimal import Decimal
from unittest.mock import MagicMock, Mock, patch
from typing import Dict, List, Any

try:
    import pandas as pd
except ImportError:
    pd = None

from boursa_vision.application.services.recommendation.recommendation_service import (
    ArchivedRecommendation,
    ArchiveDataRepository,
    TechnicalAnalyzer,
    ArchiveBasedRecommendationService,
)


class TestArchivedRecommendation:
    """Test ArchivedRecommendation dataclass."""

    def test_archived_recommendation_creation(self):
        """Test creating an ArchivedRecommendation instance."""
        # Arrange & Act
        recommendation = ArchivedRecommendation(
            symbol="AAPL",
            name="Apple Inc.",
            current_price=150.50,
            recommendation="BUY",
            overall_score=85.5,
            confidence=0.92,
            risk_level="MODERATE",
            technical_score=82.3,
            momentum_score=78.9,
            volume_score=88.1,
            price_change_1d=2.5,
            price_change_7d=5.8,
            price_change_30d=12.3,
            volatility=15.2,
            avg_volume=50000000,
            volume_trend="INCREASING",
            strengths=["Strong momentum", "Above moving averages"],
            weaknesses=["High volatility"],
            key_insights=["RSI indicates oversold conditions", "Volume surge detected"]
        )

        # Assert
        assert recommendation.symbol == "AAPL"
        assert recommendation.name == "Apple Inc."
        assert abs(recommendation.current_price - 150.50) < 0.01
        assert recommendation.recommendation == "BUY"
        assert abs(recommendation.overall_score - 85.5) < 0.01
        assert abs(recommendation.confidence - 0.92) < 0.01
        assert recommendation.risk_level == "MODERATE"
        assert abs(recommendation.technical_score - 82.3) < 0.01
        assert abs(recommendation.momentum_score - 78.9) < 0.01
        assert abs(recommendation.volume_score - 88.1) < 0.01
        assert abs(recommendation.price_change_1d - 2.5) < 0.01
        assert abs(recommendation.price_change_7d - 5.8) < 0.01
        assert abs(recommendation.price_change_30d - 12.3) < 0.01
        assert abs(recommendation.volatility - 15.2) < 0.01
        assert recommendation.avg_volume == 50000000
        assert recommendation.volume_trend == "INCREASING"
        assert len(recommendation.strengths) == 2
        assert len(recommendation.weaknesses) == 1
        assert len(recommendation.key_insights) == 2


class TestArchiveDataRepository:
    """Test ArchiveDataRepository for database operations."""

    def test_repository_initialization(self):
        """Test repository initialization with database URL."""
        # Arrange & Act
        repository = ArchiveDataRepository("postgresql://user:pass@localhost/db")

        # Assert
        assert repository.database_url == "postgresql://user:pass@localhost/db"

    @patch('psycopg2.connect')
    def test_get_connection_success(self, mock_connect):
        """Test successful database connection."""
        # Arrange
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        repository = ArchiveDataRepository("postgresql://user:pass@localhost/db")

        # Act
        connection = repository.get_connection()

        # Assert
        assert connection == mock_conn
        mock_connect.assert_called_once_with("postgresql://user:pass@localhost/db")

    @patch('psycopg2.connect')
    def test_get_available_symbols_success(self, mock_connect):
        """Test retrieving available symbols from database."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_cursor.fetchall.return_value = [('AAPL',), ('GOOGL',), ('MSFT',)]
        mock_connect.return_value = mock_conn

        repository = ArchiveDataRepository("postgresql://user:pass@localhost/db")

        # Act
        symbols = repository.get_available_symbols()

        # Assert
        assert symbols == ['AAPL', 'GOOGL', 'MSFT']
        mock_cursor.execute.assert_called_once()
        assert "SELECT DISTINCT i.symbol" in mock_cursor.execute.call_args[0][0]

    @patch('psycopg2.connect')
    def test_get_available_symbols_empty(self, mock_connect):
        """Test retrieving symbols when database is empty."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_cursor.fetchall.return_value = []
        mock_connect.return_value = mock_conn

        repository = ArchiveDataRepository("postgresql://user:pass@localhost/db")

        # Act
        symbols = repository.get_available_symbols()

        # Assert
        assert symbols == []
        mock_cursor.execute.assert_called_once()

    @patch('pandas.read_sql_query')
    @patch('psycopg2.connect')
    def test_get_market_data_success(self, mock_connect, mock_read_sql):
        """Test retrieving market data for a symbol."""
        # Arrange
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_connect.return_value = mock_conn
        
        # Create sample data without using pandas directly
        if pd:
            sample_data = pd.DataFrame({
                'time': ['2024-01-01 10:00:00', '2024-01-02 10:00:00'],
                'open': [100.0, 101.0],
                'high': [105.0, 106.0],
                'low': [99.0, 100.0],
                'close': [104.0, 105.0],
                'volume': [1000000, 1100000]
            })
        else:
            sample_data = Mock()
            sample_data.__len__ = lambda: 2
        
        mock_read_sql.return_value = sample_data

        repository = ArchiveDataRepository("postgresql://user:pass@localhost/db")

        # Act
        result = repository.get_market_data("AAPL", days=30)

        # Assert
        assert len(result) == 2
        mock_read_sql.assert_called_once()
        assert mock_read_sql.call_args[1]['params'] == ("AAPL", 30)

    @patch('pandas.read_sql_query')
    @patch('psycopg2.connect')
    def test_get_market_data_empty(self, mock_connect, mock_read_sql):
        """Test retrieving market data when no data exists."""
        # Arrange
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_connect.return_value = mock_conn
        
        if pd:
            empty_data = pd.DataFrame()
        else:
            empty_data = Mock()
            empty_data.empty = True
        
        mock_read_sql.return_value = empty_data

        repository = ArchiveDataRepository("postgresql://user:pass@localhost/db")

        # Act
        result = repository.get_market_data("NONEXISTENT", days=30)

        # Assert
        assert result.empty
        mock_read_sql.assert_called_once()

    @patch('psycopg2.connect')
    def test_get_symbol_info_success(self, mock_connect):
        """Test retrieving symbol information."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_cursor.fetchone.return_value = ('AAPL', 'Apple Inc.', 'stock', 'USD')
        mock_connect.return_value = mock_conn

        repository = ArchiveDataRepository("postgresql://user:pass@localhost/db")

        # Act
        result = repository.get_symbol_info("AAPL")

        # Assert
        assert result == {
            'symbol': 'AAPL',
            'name': 'Apple Inc.',
            'instrument_type': 'stock',
            'currency': 'USD'
        }
        mock_cursor.execute.assert_called_once_with(
            mock_cursor.execute.call_args[0][0], ('AAPL',)
        )

    @patch('psycopg2.connect')
    def test_get_symbol_info_not_found(self, mock_connect):
        """Test retrieving symbol information for non-existent symbol."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_cursor.fetchone.return_value = None
        mock_connect.return_value = mock_conn

        repository = ArchiveDataRepository("postgresql://user:pass@localhost/db")

        # Act
        result = repository.get_symbol_info("NONEXISTENT")

        # Assert
        assert result == {}
        mock_cursor.execute.assert_called_once()

    @patch('psycopg2.connect')
    def test_get_symbol_info_with_nulls(self, mock_connect):
        """Test retrieving symbol information with null values."""
        # Arrange
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.__enter__.return_value = mock_conn
        mock_conn.__exit__.return_value = None
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        mock_conn.cursor.return_value.__exit__.return_value = None
        mock_cursor.fetchone.return_value = ('TEST', None, None, None)
        mock_connect.return_value = mock_conn

        repository = ArchiveDataRepository("postgresql://user:pass@localhost/db")

        # Act
        result = repository.get_symbol_info("TEST")

        # Assert
        assert result == {
            'symbol': 'TEST',
            'name': 'TEST Security',
            'instrument_type': 'stock',
            'currency': 'USD'
        }


class TestTechnicalAnalyzer:
    """Test TechnicalAnalyzer for financial calculations."""

    def test_calculate_rsi_normal_conditions(self):
        """Test RSI calculation under normal conditions."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")
        
        prices = pd.Series([100, 102, 101, 103, 104, 102, 105, 107, 106, 108, 110,
                           109, 111, 113, 112, 114, 116, 115, 117, 119])

        # Act
        rsi = TechnicalAnalyzer.calculate_rsi(prices)

        # Assert
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100
        assert rsi > 50  # Upward trend should have RSI > 50

    def test_calculate_rsi_insufficient_data(self):
        """Test RSI calculation with insufficient data."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")
        
        prices = pd.Series([100, 102, 101])  # Less than period + 1

        # Act
        rsi = TechnicalAnalyzer.calculate_rsi(prices, period=14)

        # Assert
        assert abs(rsi - 50.0) < 0.01  # Should return neutral RSI

    def test_calculate_rsi_custom_period(self):
        """Test RSI calculation with custom period."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")
        
        prices = pd.Series([100, 102, 101, 103, 104, 102, 105])

        # Act
        rsi = TechnicalAnalyzer.calculate_rsi(prices, period=5)

        # Assert
        assert isinstance(rsi, float)
        assert 0 <= rsi <= 100

    def test_calculate_rsi_with_nan_values(self):
        """Test RSI calculation when result contains NaN."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")
        
        prices = pd.Series([100.0] * 20)  # Flat prices - no gains/losses

        # Act
        rsi = TechnicalAnalyzer.calculate_rsi(prices)

        # Assert
        assert abs(rsi - 50.0) < 0.01  # Should return neutral RSI for NaN

    def test_calculate_moving_averages_normal_data(self):
        """Test moving averages calculation with sufficient data."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")
        
        prices = pd.Series(list(range(100, 160)))  # 60 data points

        # Act
        mas = TechnicalAnalyzer.calculate_moving_averages(prices)

        # Assert
        assert 'ma_5' in mas
        assert 'ma_10' in mas
        assert 'ma_20' in mas
        assert 'ma_50' in mas
        assert all(isinstance(ma, float) for ma in mas.values())
        assert mas['ma_5'] > mas['ma_50']  # Short MA should be higher in uptrend

    def test_calculate_moving_averages_insufficient_data(self):
        """Test moving averages with insufficient data for some periods."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")
        
        prices = pd.Series([100, 102, 104])  # Only 3 data points

        # Act
        mas = TechnicalAnalyzer.calculate_moving_averages(prices)

        # Assert
        assert 'ma_5' in mas
        assert 'ma_10' in mas
        assert 'ma_20' in mas
        assert 'ma_50' in mas
        # All should use mean when insufficient data
        expected_mean = prices.mean()
        assert abs(mas['ma_50'] - expected_mean) < 0.01

    def test_calculate_volatility_normal_data(self):
        """Test volatility calculation with normal price data."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")
        
        prices = pd.Series([100, 102, 98, 105, 99, 103, 97, 106, 95, 108,
                           92, 110, 89, 112, 87, 115, 85, 118, 83, 120])

        # Act
        volatility = TechnicalAnalyzer.calculate_volatility(prices)

        # Assert
        assert isinstance(volatility, float)
        assert volatility > 0  # Should have positive volatility

    def test_calculate_volatility_insufficient_data(self):
        """Test volatility calculation with insufficient data."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")
        
        prices = pd.Series([100])  # Single data point

        # Act
        volatility = TechnicalAnalyzer.calculate_volatility(prices)

        # Assert
        assert abs(volatility - 0.0) < 0.01

    def test_calculate_volatility_custom_period(self):
        """Test volatility calculation with custom period."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")
        
        prices = pd.Series([100, 102, 98, 105, 99, 103])

        # Act
        volatility = TechnicalAnalyzer.calculate_volatility(prices, period=3)

        # Assert
        assert isinstance(volatility, float)
        assert volatility >= 0

    def test_calculate_volatility_stable_prices(self):
        """Test volatility calculation with stable prices."""
        # Arrange
        if not pd:
            pytest.skip("pandas not available")
        
        prices = pd.Series([100.0] * 20)  # Flat prices

        # Act
        volatility = TechnicalAnalyzer.calculate_volatility(prices)

        # Assert
        assert abs(volatility - 0.0) < 0.01  # No volatility for flat prices


class TestArchiveBasedRecommendationService:
    """Test ArchiveBasedRecommendationService main functionality."""

    @pytest.fixture
    def mock_repository(self):
        """Mock repository for testing."""
        repository = Mock(spec=ArchiveDataRepository)
        return repository

    @pytest.fixture
    def mock_analyzer(self):
        """Mock technical analyzer for testing."""
        analyzer = Mock(spec=TechnicalAnalyzer)
        return analyzer

    @pytest.fixture
    def service(self, mock_repository, mock_analyzer):
        """Create service with mocked dependencies."""
        with patch('boursa_vision.application.services.recommendation.recommendation_service.ArchiveDataRepository') as mock_repo_class:
            with patch('boursa_vision.application.services.recommendation.recommendation_service.TechnicalAnalyzer') as mock_analyzer_class:
                mock_repo_class.return_value = mock_repository
                mock_analyzer_class.return_value = mock_analyzer
                
                service = ArchiveBasedRecommendationService("test_db_url")
                service.repository = mock_repository
                service.technical_analyzer = mock_analyzer
                return service

    def test_service_initialization(self):
        """Test service initialization."""
        # Act
        service = ArchiveBasedRecommendationService("postgresql://test:test@localhost/test")

        # Assert
        assert service.repository is not None
        assert service.technical_analyzer is not None

    def test_get_recommendations_success(self, service, mock_repository):
        """Test successful recommendations generation."""
        # Arrange
        mock_repository.get_available_symbols.return_value = ['AAPL', 'GOOGL']
        
        # Mock _analyze_symbol to return valid recommendations
        high_score_rec = ArchivedRecommendation(
            symbol="AAPL", name="Apple Inc.", current_price=150.0,
            recommendation="BUY", overall_score=85.0, confidence=0.9,
            risk_level="MODERATE", technical_score=80.0, momentum_score=85.0,
            volume_score=90.0, price_change_1d=2.0, price_change_7d=5.0,
            price_change_30d=10.0, volatility=15.0, avg_volume=50000000,
            volume_trend="INCREASING", strengths=["Strong momentum"],
            weaknesses=[], key_insights=["RSI oversold"]
        )
        
        low_score_rec = ArchivedRecommendation(
            symbol="GOOGL", name="Alphabet Inc.", current_price=120.0,
            recommendation="HOLD", overall_score=55.0, confidence=0.7,
            risk_level="LOW", technical_score=50.0, momentum_score=60.0,
            volume_score=55.0, price_change_1d=-1.0, price_change_7d=1.0,
            price_change_30d=3.0, volatility=10.0, avg_volume=30000000,
            volume_trend="STABLE", strengths=[], weaknesses=["Weak momentum"],
            key_insights=["Neutral trend"]
        )

        service._analyze_symbol = Mock(side_effect=[high_score_rec, low_score_rec])

        # Act
        recommendations = service.get_recommendations(max_recommendations=5, min_score=60.0)

        # Assert
        assert len(recommendations) == 1  # Only high score rec meets min_score
        assert recommendations[0].symbol == "AAPL"
        assert abs(recommendations[0].overall_score - 85.0) < 0.01

    def test_get_recommendations_empty_symbols(self, service, mock_repository):
        """Test recommendations with no available symbols."""
        # Arrange
        mock_repository.get_available_symbols.return_value = []

        # Act
        recommendations = service.get_recommendations()

        # Assert
        assert recommendations == []

    def test_get_recommendations_analysis_errors(self, service, mock_repository):
        """Test recommendations when analysis fails."""
        # Arrange
        mock_repository.get_available_symbols.return_value = ['ERROR_SYMBOL']
        service._analyze_symbol = Mock(side_effect=Exception("Analysis error"))

        # Act
        recommendations = service.get_recommendations()

        # Assert
        assert recommendations == []
