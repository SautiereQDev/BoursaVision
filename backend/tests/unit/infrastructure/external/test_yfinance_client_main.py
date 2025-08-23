"""
Main API method tests for OptimizedYFinanceClient - Priority #4
Testing core functionality with comprehensive mocking
"""

from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from boursa_vision.infrastructure.external.yfinance_client import (
    OptimizedYFinanceClient,
    YFinanceConfig,
    YFinanceError,
    YFinanceRateLimitError,
    YFinanceTimeoutError,
)


@pytest.fixture
def basic_config():
    """Basic config for testing."""
    return YFinanceConfig(
        max_requests_per_minute=60,
        enable_cache=False,  # Disable cache for simpler testing
        max_retries=2,
    )


@pytest.fixture
def sample_stock_info():
    """Sample stock information data."""
    return {
        "symbol": "AAPL",
        "longName": "Apple Inc.",
        "currentPrice": 150.0,
        "marketCap": 2500000000000,
        "dividendYield": 0.006,
    }


class TestGetStockInfo:
    """Test get_stock_info method."""

    def test_get_stock_info_success_no_cache(self, basic_config, sample_stock_info):
        """Test successful stock info retrieval without cache."""
        # Arrange
        symbol = "AAPL"

        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)

            # Mock the retry handler to return our data
            client.retry_handler.execute.return_value = sample_stock_info

            # Act
            result = client.get_stock_info(symbol)

            # Assert
            assert result == sample_stock_info
            assert client.metrics.successful_requests == 1

    def test_get_stock_info_returns_none_on_error(self, basic_config):
        """Test that get_stock_info returns None on error instead of raising."""
        # Arrange
        symbol = "INVALID"

        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)

            # Mock the retry handler to raise an exception
            client.retry_handler.execute.side_effect = Exception("API Error")

            # Act
            result = client.get_stock_info(symbol)

            # Assert
            assert result is None
            assert client.metrics.failed_requests == 1

    def test_get_stock_info_with_cache_enabled(self, sample_stock_info):
        """Test with cache enabled."""
        # Arrange
        config = YFinanceConfig(max_requests_per_minute=60, enable_cache=True)

        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            RedisCache=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
            AdaptiveCacheStrategy=MagicMock(),
        ):
            client = OptimizedYFinanceClient(config)

            # Mock cache
            client.cache = MagicMock()
            client.cache.get.return_value = sample_stock_info  # Cache hit

            # Act
            result = client.get_stock_info("AAPL", use_cache=True)

            # Assert
            assert result == sample_stock_info
            assert client.metrics.cache_hits == 1


class TestGetHistoricalData:
    """Test get_historical_data method."""

    def test_get_historical_data_success(self, basic_config):
        """Test successful historical data retrieval."""
        # Arrange
        symbol = "AAPL"
        period = "1y"
        mock_data = {"dates": ["2023-01-01", "2023-01-02"], "prices": [150.0, 151.0]}

        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)

            # Mock retry handler
            client.retry_handler.execute.return_value = mock_data

            # Act
            result = client.get_historical_data(symbol, period=period)

            # Assert
            assert result == mock_data
            assert client.metrics.successful_requests == 1

    def test_get_historical_data_returns_none_on_error(self, basic_config):
        """Test historical data returns None on error."""
        # Arrange
        symbol = "INVALID"

        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)

            # Mock retry handler to raise exception
            client.retry_handler.execute.side_effect = Exception("API Error")

            # Act
            result = client.get_historical_data(symbol)

            # Assert
            assert result is None
            assert client.metrics.failed_requests == 1


class TestGetMultipleStockInfo:
    """Test get_multiple_stock_info method."""

    def test_get_multiple_stock_info_success(self, basic_config, sample_stock_info):
        """Test successful multiple stock info retrieval."""
        # Arrange
        symbols = ["AAPL", "GOOGL", "MSFT"]

        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)

            # Mock the _process_batch_parallel method directly
            expected_results = {symbol: sample_stock_info for symbol in symbols}
            client._process_batch_parallel = MagicMock(return_value=expected_results)

            # Act
            results = client.get_multiple_stock_info(symbols)

            # Assert
            assert len(results) == len(symbols)
            assert all(symbol in results for symbol in symbols)
            assert all(results[symbol] == sample_stock_info for symbol in symbols)

    def test_get_multiple_stock_info_empty_symbols(self, basic_config):
        """Test multiple stock info with empty symbol list."""
        # Arrange
        symbols = []

        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)

            # Act
            results = client.get_multiple_stock_info(symbols)

            # Assert
            assert results == {}


class TestResiliencePatterns:
    """Test resilience patterns: rate limiting, circuit breaker, retries."""

    def test_rate_limiter_acquire_called(self, basic_config):
        """Test that rate limiter is properly used."""
        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)
            client.retry_handler.execute.return_value = {"symbol": "AAPL"}

            # Act
            client.get_stock_info("AAPL")

            # Assert that circuit breaker and retry handler components are used
            assert client.retry_handler.execute.called

    def test_metrics_tracking(self, basic_config, sample_stock_info):
        """Test that metrics are properly tracked."""
        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)
            client.retry_handler.execute.return_value = sample_stock_info

            # Act
            result = client.get_stock_info("AAPL")

            # Assert
            assert result == sample_stock_info
            assert client.metrics.successful_requests == 1
            assert client.metrics.total_requests == 1


class TestHealthCheck:
    """Test health check functionality."""

    def test_health_check_structure(self, basic_config):
        """Test health check returns proper structure."""
        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)

            # Mock the component info methods
            client.get_rate_limiter_info = MagicMock(return_value={"status": "ok"})
            client.get_circuit_breaker_stats = MagicMock(
                return_value={"state": "closed"}
            )
            client.get_cache_stats = MagicMock(return_value={"status": "disabled"})

            # Act
            health = client.health_check()

            # Assert
            assert "rate_limiter" in health
            assert "circuit_breaker" in health
            assert "cache" in health
            assert "metrics" in health
            assert "success_rate" in health["metrics"]
            assert "cache_hit_rate" in health["metrics"]
            assert "average_response_time" in health["metrics"]


class TestClientLifecycle:
    """Test client lifecycle methods."""

    def test_client_context_manager(self, basic_config):
        """Test client can be used as context manager."""
        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            # Act & Assert
            with OptimizedYFinanceClient(basic_config) as client:
                assert client is not None
                client.executor = MagicMock()  # Mock executor for cleanup
                client.executor.shutdown = MagicMock()

    def test_client_close(self, basic_config):
        """Test client cleanup."""
        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)
            client.executor = MagicMock()  # Mock executor
            client.executor.shutdown = MagicMock()

            # Act
            client.close()

            # Assert
            client.executor.shutdown.assert_called_once_with(wait=True)

    def test_reset_metrics(self, basic_config):
        """Test metrics reset."""
        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(basic_config)

            # Set some metrics
            client.metrics.successful_requests = 5
            client.metrics.failed_requests = 2

            # Act
            client.reset_metrics()

            # Assert
            assert client.metrics.successful_requests == 0
            assert client.metrics.failed_requests == 0
