"""
Market data fixtures for API testing.

Following architecture in TESTS.md:
- Fixtures communes réutilisables
- Mock data for YFinance responses
- HTTP client fixtures for FastAPI testing
"""

from datetime import UTC, datetime
from typing import Any
from unittest.mock import Mock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def mock_yfinance_ticker_info() -> dict[str, Any]:
    """Mock YFinance ticker info response."""
    return {
        "symbol": "AAPL",
        "longName": "Apple Inc.",
        "currency": "USD",
        "exchange": "NASDAQ",
        "sector": "Technology",
        "marketCap": 2800000000000,
        "currentPrice": 150.75,
        "previousClose": 149.50,
        "dayLow": 148.25,
        "dayHigh": 151.00,
        "volume": 75000000,
        "averageVolume": 85000000,
        "dividendYield": 0.0052,
        "payoutRatio": 0.15,
        "beta": 1.2,
        "trailingPE": 28.5,
        "forwardPE": 25.2,
        "pegRatio": 2.1,
        "priceToBook": 45.8,
        "returnOnEquity": 1.47,
        "debtToEquity": 261.4,
        "grossMargins": 0.41,
        "operatingMargins": 0.30,
        "revenueGrowth": 0.08,
        "earningsGrowth": 0.10,
        "recommendationKey": "buy",
        "recommendationMean": 2.1,
        "targetHighPrice": 180.0,
        "targetLowPrice": 140.0,
        "targetMeanPrice": 160.0,
        "fiftyTwoWeekLow": 124.17,
        "fiftyTwoWeekHigh": 182.94,
        "fiftyDayAverage": 145.32,
        "twoHundredDayAverage": 155.67,
    }


@pytest.fixture
def mock_yfinance_history_data():
    """Mock YFinance historical data response."""
    dates = pd.date_range(start="2024-01-01", end="2024-01-31", freq="D")[:20]
    return pd.DataFrame(
        {
            "Open": [148.0 + i * 0.5 for i in range(20)],
            "High": [150.0 + i * 0.5 for i in range(20)],
            "Low": [147.0 + i * 0.5 for i in range(20)],
            "Close": [149.0 + i * 0.5 for i in range(20)],
            "Volume": [75000000 + i * 1000000 for i in range(20)],
        },
        index=dates,
    )


@pytest.fixture
def mock_yfinance_empty_data():
    """Mock empty YFinance response for invalid symbols."""
    return pd.DataFrame()


@pytest.fixture
def mock_yfinance_ticker(mock_yfinance_ticker_info, mock_yfinance_history_data):
    """Mock YFinance Ticker object."""
    mock_ticker = Mock()
    mock_ticker.info = mock_yfinance_ticker_info
    mock_ticker.history.return_value = mock_yfinance_history_data
    return mock_ticker


@pytest.fixture
def mock_yfinance_ticker_not_found():
    """Mock YFinance Ticker object for not found symbols."""
    mock_ticker = Mock()
    mock_ticker.info = {}
    mock_ticker.history.return_value = pd.DataFrame()
    return mock_ticker


@pytest.fixture
def mock_yfinance_ticker_error():
    """Mock YFinance Ticker object that raises exceptions."""
    mock_ticker = Mock()
    mock_ticker.info.side_effect = Exception("Network error")
    mock_ticker.history.side_effect = Exception("Network error")
    return mock_ticker


@pytest.fixture
def mock_recommendation_service():
    """Mock investment recommendation service."""
    mock_service = Mock()
    mock_service.get_best_investments.return_value = [
        {
            "symbol": "AAPL",
            "score": 0.85,
            "recommendation": "BUY",
            "target_price": 160.0,
            "risk_level": "LOW",
        },
        {
            "symbol": "MSFT",
            "score": 0.82,
            "recommendation": "BUY",
            "target_price": 380.0,
            "risk_level": "LOW",
        },
    ]
    mock_service.quick_analyze.return_value = {
        "symbol": "AAPL",
        "analysis": "Strong fundamentals with good growth prospects",
        "score": 0.85,
        "recommendation": "BUY",
        "confidence": 0.78,
    }
    return mock_service


@pytest.fixture
def api_client():
    """Test client for FastAPI application."""
    # Import here to avoid circular imports during testing
    try:
        from src.boursa_vision.presentation.api.v1.market_api import app

        return TestClient(app)
    except ImportError:
        # Skip if module not available
        pytest.skip("market_api module not available for testing")


@pytest.fixture
def valid_ticker_symbols():
    """List of valid ticker symbols for testing."""
    return ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN"]


@pytest.fixture
def invalid_ticker_symbols():
    """List of invalid ticker symbols for testing."""
    return ["INVALID", "NOTEXIST", "123ABC", "", "   "]


@pytest.fixture
def financial_indices():
    """Financial indices data for testing."""
    return {
        "cac40": ["MC.PA", "ASML.AS", "OR.PA"],
        "nasdaq100": ["AAPL", "MSFT", "AMZN"],
    }


@pytest.fixture
def mock_datetime_now():
    """Mock datetime.now for consistent timestamps in tests."""
    fixed_datetime = datetime(2024, 8, 21, 12, 0, 0, tzinfo=UTC)
    with patch("boursa_vision.presentation.api.v1.market_api.datetime") as mock_dt:
        mock_dt.now.return_value = fixed_datetime
        yield fixed_datetime


@pytest.fixture
def expected_api_info_response():
    """Expected API info response structure."""
    return {
        "service": "Boursa Vision - Advanced Investment Analysis API",
        "version": "2.0.0",
        "description": "Real financial data with comprehensive analysis using YFinance and advanced algorithms",
        "timestamp": "2024-08-21T12:00:00+00:00",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_schema": "/openapi.json",
        },
        "configuration": {
            "enabled_indices": ["cac40", "nasdaq100"],
            "total_symbols": pytest.approx(140, abs=20),  # Approximative count
            "advanced_analysis_available": True,
        },
    }


@pytest.fixture
def expected_health_check_response():
    """Expected health check response structure."""
    return {
        "status": "healthy",
        "timestamp": "2024-08-21T12:00:00+00:00",
        "real_data_tests": {
            "apple_info_available": True,
            "microsoft_info_available": True,
            "test_symbols_processed": 2,
        },
        "summary": {
            "api_operational": True,
            "data_source_healthy": True,
            "response_time_ms": pytest.approx(100, abs=200),
        },
    }
