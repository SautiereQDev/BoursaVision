"""
Basic infrastructure tests for OptimizedYFinanceClient - Priority #4 
Testing configuration, metrics, and exception classes
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from boursa_vision.infrastructure.external.yfinance_client import (
    OptimizedYFinanceClient,
    RequestMetrics,
    YFinanceConfig,
    YFinanceError,
    YFinanceRateLimitError,
    YFinanceTimeoutError,
)


class TestYFinanceConfig:
    """Test YFinanceConfig dataclass."""

    def test_yfinance_config_default_values(self):
        """Test default configuration values."""
        config = YFinanceConfig()

        # Default values
        assert config.max_requests_per_minute == 2000
        assert config.rate_limit_window == 60
        assert config.max_concurrent_requests == 50
        assert config.request_timeout == 30.0
        assert config.max_retries == 3
        assert config.retry_base_delay == 1.0
        assert config.retry_max_delay == 60.0
        assert config.circuit_breaker_failure_threshold == 5
        assert config.circuit_breaker_recovery_timeout == 60.0
        assert config.enable_cache is True
        assert config.cache_config is None
        assert config.batch_size == 10

    def test_yfinance_config_custom_values(self):
        """Test configuration with custom values."""
        config = YFinanceConfig(
            max_requests_per_minute=100,
            request_timeout=15.0,
            max_retries=5,
            enable_cache=False,
        )

        assert config.max_requests_per_minute == 100
        assert config.request_timeout == 15.0
        assert config.max_retries == 5
        assert config.enable_cache is False
        # Other values should remain default
        assert config.rate_limit_window == 60
        assert config.batch_size == 10


class TestRequestMetrics:
    """Test RequestMetrics class."""

    def test_request_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = RequestMetrics()

        assert metrics.successful_requests == 0
        assert metrics.failed_requests == 0
        assert metrics.total_requests == 0
        assert metrics.cache_hits == 0
        assert metrics.cache_misses == 0
        assert metrics.rate_limit_errors == 0
        assert metrics.circuit_breaker_trips == 0
        assert metrics.average_response_time == 0.0

    def test_success_rate_calculation_zero_requests(self):
        """Test success rate calculation with zero requests."""
        metrics = RequestMetrics()

        assert metrics.success_rate() == 0.0

    def test_success_rate_calculation_with_requests(self):
        """Test success rate calculation with some requests."""
        metrics = RequestMetrics()
        metrics.successful_requests = 8
        metrics.failed_requests = 2
        metrics.total_requests = 10

        assert abs(metrics.success_rate() - 80.0) < 0.001

    def test_cache_hit_rate_calculation_zero_cache_requests(self):
        """Test cache hit rate with no cache requests."""
        metrics = RequestMetrics()

        assert metrics.cache_hit_rate() == 0.0

    def test_cache_hit_rate_calculation_with_cache_requests(self):
        """Test cache hit rate calculation with cache requests."""
        metrics = RequestMetrics()
        metrics.cache_hits = 7
        metrics.cache_misses = 3

        assert abs(metrics.cache_hit_rate() - 70.0) < 0.001


class TestYFinanceExceptions:
    """Test exception hierarchy."""

    def test_yfinance_error_inheritance(self):
        """Test YFinanceError inheritance."""
        error = YFinanceError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

    def test_yfinance_rate_limit_error_inheritance(self):
        """Test YFinanceRateLimitError inheritance."""
        error = YFinanceRateLimitError("rate limit")
        assert isinstance(error, YFinanceError)
        assert isinstance(error, Exception)
        assert str(error) == "rate limit"

    def test_yfinance_timeout_error_inheritance(self):
        """Test YFinanceTimeoutError inheritance."""
        error = YFinanceTimeoutError("timeout")
        assert isinstance(error, YFinanceError)
        assert isinstance(error, Exception)
        assert str(error) == "timeout"


class TestYFinanceClientIntegration:
    """Test basic client integration with infrastructure components."""

    def test_config_dataclass_functionality(self):
        """Test that config works as a dataclass."""
        config = YFinanceConfig()

        # Test field access
        assert hasattr(config, "max_requests_per_minute")
        assert hasattr(config, "enable_cache")

        # Test modification
        config.max_requests_per_minute = 500
        assert config.max_requests_per_minute == 500

    def test_metrics_calculations(self):
        """Test metrics calculation methods."""
        metrics = RequestMetrics()

        # Test empty metrics
        assert metrics.success_rate() == 0.0
        assert metrics.cache_hit_rate() == 0.0
        assert metrics.average_response_time == 0.0

        # Add some data
        metrics.successful_requests = 5
        metrics.total_requests = 10
        metrics.cache_hits = 3
        metrics.cache_misses = 2
        metrics.average_response_time = 2.0

        # Test calculations
        assert abs(metrics.success_rate() - 50.0) < 0.001
        assert abs(metrics.cache_hit_rate() - 60.0) < 0.001
        assert metrics.average_response_time == 2.0

    def test_exception_hierarchy(self):
        """Test exception hierarchy is correctly set up."""
        # Base exception
        base_error = YFinanceError("base")
        assert isinstance(base_error, Exception)

        # Rate limit error
        rate_error = YFinanceRateLimitError("rate")
        assert isinstance(rate_error, YFinanceError)
        assert isinstance(rate_error, Exception)

        # Timeout error
        timeout_error = YFinanceTimeoutError("timeout")
        assert isinstance(timeout_error, YFinanceError)
        assert isinstance(timeout_error, Exception)


class TestOptimizedYFinanceClientBasics:
    """Test basic client instantiation and configuration."""

    def test_client_initialization_mocked(self):
        """Test client initialization with mocked dependencies."""
        config = YFinanceConfig(enable_cache=False)

        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(config)

            assert client.config == config
            assert hasattr(client, "metrics")
            assert client.cache is None  # Cache disabled
            assert hasattr(client, "executor")

    def test_client_with_custom_config(self):
        """Test client with custom configuration."""
        config = YFinanceConfig(
            max_requests_per_minute=100, enable_cache=False, max_concurrent_requests=5
        )

        with patch.multiple(
            "boursa_vision.infrastructure.external.yfinance_client",
            yf=MagicMock(),
            AdaptiveRateLimiter=MagicMock(),
            CircuitBreaker=MagicMock(),
            RetryHandler=MagicMock(),
            ThreadPoolExecutor=MagicMock(),
        ):
            client = OptimizedYFinanceClient(config)

            assert client.config.max_requests_per_minute == 100
            assert client.config.max_concurrent_requests == 5
            assert client.config.enable_cache is False
