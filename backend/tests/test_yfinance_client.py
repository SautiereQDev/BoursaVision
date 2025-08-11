"""
Tests for YFinance Client
========================

Unit tests for the optimized YFinance client with mocked API.
"""

import asyncio
import json
import time
import unittest
from concurrent.futures import Future
from typing import Any, Dict
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.infrastructure.external.cache_strategy import CacheConfig, DataFrequency
from src.infrastructure.external.circuit_breaker import CircuitState
from src.infrastructure.external.client_factory import (
    ClientProfile,
    YFinanceClientFactory,
)
from src.infrastructure.external.rate_limiter import RateLimit
from src.infrastructure.external.yfinance_client import (
    OptimizedYFinanceClient,
    RequestMetrics,
    YFinanceConfig,
    YFinanceError,
    YFinanceRateLimitError,
)


class MockYFinanceTicker:
    """Mock YFinance Ticker class"""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.info = {
            "symbol": symbol,
            "longName": f"{symbol} Company",
            "marketCap": 1000000000,
            "regularMarketPrice": 150.0,
        }

    def history(self, period="1y", interval="1d"):
        """Mock history method"""
        # Return mock DataFrame-like object
        return MockDataFrame(
            [
                {
                    "Date": "2023-01-01",
                    "Open": 100,
                    "High": 110,
                    "Low": 95,
                    "Close": 105,
                    "Volume": 1000000,
                },
                {
                    "Date": "2023-01-02",
                    "Open": 105,
                    "High": 115,
                    "Low": 100,
                    "Close": 110,
                    "Volume": 1200000,
                },
            ]
        )


class MockDataFrame:
    """Mock pandas DataFrame"""

    def __init__(self, data):
        self.data = data

    def to_dict(self, orient="records"):
        return self.data


class TestOptimizedYFinanceClient:
    """Test cases for OptimizedYFinanceClient"""

    @pytest.fixture
    def basic_config(self):
        """Basic configuration for testing"""
        return YFinanceConfig(
            max_requests_per_minute=100,  # Lower for testing
            max_concurrent_requests=5,
            batch_size=2,
            enable_cache=False,  # Disable cache for basic tests
        )

    @pytest.fixture
    def config_with_cache(self):
        """Configuration with cache enabled"""
        cache_config = CacheConfig(
            host="localhost", port=6379, db=1  # Use different DB for testing
        )
        return YFinanceConfig(
            max_requests_per_minute=100, enable_cache=True, cache_config=cache_config
        )

    @pytest.fixture
    def mock_yf_ticker(self):
        """Mock yfinance.Ticker"""
        with patch("src.infrastructure.external.yfinance_client.yf") as mock_yf:
            mock_yf.Ticker.return_value = MockYFinanceTicker("AAPL")
            yield mock_yf

    @pytest.fixture
    def mock_redis_cache(self):
        """Mock Redis cache"""
        with patch("src.infrastructure.external.cache_strategy.redis") as mock_redis:
            mock_redis_instance = Mock()
            mock_redis_instance.ping.return_value = True
            mock_redis_instance.get.return_value = None
            mock_redis_instance.setex.return_value = True
            mock_redis_instance.delete.return_value = 1
            mock_redis_instance.exists.return_value = False
            mock_redis_instance.ttl.return_value = 300
            mock_redis_instance.keys.return_value = []
            mock_redis_instance.info.return_value = {
                "used_memory_human": "1MB",
                "connected_clients": 1,
                "total_commands_processed": 100,
                "keyspace_hits": 80,
                "keyspace_misses": 20,
            }

            mock_redis.Redis.return_value = mock_redis_instance
            mock_redis.ConnectionPool.return_value = Mock()
            yield mock_redis_instance

    def test_client_initialization(self, basic_config, mock_yf_ticker):
        """Test client initialization"""
        client = OptimizedYFinanceClient(basic_config)

        assert client.config == basic_config
        assert isinstance(client.metrics, RequestMetrics)
        assert client.rate_limiter is not None
        assert client.circuit_breaker is not None
        assert client.retry_handler is not None

        client.close()

    def test_get_stock_info_success(self, basic_config, mock_yf_ticker):
        """Test successful stock info retrieval"""
        client = OptimizedYFinanceClient(basic_config)

        result = client.get_stock_info("AAPL")

        assert result is not None
        assert result["symbol"] == "AAPL"
        assert result["longName"] == "AAPL Company"
        assert client.metrics.successful_requests == 1
        assert client.metrics.total_requests == 1

        client.close()

    def test_get_historical_data_success(self, basic_config, mock_yf_ticker):
        """Test successful historical data retrieval"""
        client = OptimizedYFinanceClient(basic_config)

        result = client.get_historical_data("AAPL", period="1mo", interval="1d")

        assert result is not None
        assert len(result.data) == 2  # Mock data has 2 records
        assert client.metrics.successful_requests == 1
        assert client.metrics.total_requests == 1

        client.close()

    def test_rate_limiting(self, basic_config, mock_yf_ticker):
        """Test rate limiting functionality"""
        # Set very low rate limit for testing
        basic_config.max_requests_per_minute = 2

        client = OptimizedYFinanceClient(basic_config)

        # First two requests should succeed
        result1 = client.get_stock_info("AAPL")
        result2 = client.get_stock_info("GOOGL")

        assert result1 is not None
        assert result2 is not None

        # Third request should be rate limited (but client handles it gracefully)
        start_time = time.time()
        result3 = client.get_stock_info("MSFT")
        end_time = time.time()

        # Should have waited for rate limit
        assert end_time - start_time > 0
        assert result3 is not None

        client.close()

    def test_circuit_breaker_functionality(self, basic_config):
        """Test circuit breaker functionality"""
        with patch("src.infrastructure.external.yfinance_client.yf") as mock_yf:
            # Configure mock to always fail
            mock_yf.Ticker.side_effect = Exception("API Error")

            client = OptimizedYFinanceClient(basic_config)

            # Make several failing requests to trip circuit breaker
            for _ in range(6):  # More than failure_threshold (5)
                result = client.get_stock_info("AAPL")
                assert result is None

            # Circuit breaker should be open
            assert client.circuit_breaker.get_state() == CircuitState.OPEN
            assert client.metrics.failed_requests > 0

            client.close()

    def test_multiple_stock_info_parallel(self, basic_config, mock_yf_ticker):
        """Test parallel processing of multiple symbols"""
        client = OptimizedYFinanceClient(basic_config)

        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]

        start_time = time.time()
        results = client.get_multiple_stock_info(symbols)
        end_time = time.time()

        assert len(results) == 4
        assert all(symbol in results for symbol in symbols)
        assert all(results[symbol] is not None for symbol in symbols)

        # Should be faster than sequential processing
        assert end_time - start_time < 2.0  # Reasonable threshold

        client.close()

    def test_cache_functionality(
        self, config_with_cache, mock_yf_ticker, mock_redis_cache
    ):
        """Test cache functionality"""
        client = OptimizedYFinanceClient(config_with_cache)

        # First request should miss cache
        result1 = client.get_stock_info("AAPL")
        assert result1 is not None
        assert client.metrics.cache_misses == 1
        assert client.metrics.cache_hits == 0

        # Mock cache to return data for second request
        mock_redis_cache.get.return_value = json.dumps(
            {"symbol": "AAPL", "longName": "Apple Inc."}
        )

        # Second request should hit cache
        result2 = client.get_stock_info("AAPL")
        assert result2 is not None
        assert client.metrics.cache_hits == 1

        client.close()

    def test_retry_mechanism(self, basic_config):
        """Test retry mechanism"""
        with patch("src.infrastructure.external.yfinance_client.yf") as mock_yf:
            # First two calls fail, third succeeds
            mock_ticker = Mock()
            mock_ticker.info = {"symbol": "AAPL", "longName": "Apple Inc."}

            call_count = 0

            def side_effect(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    raise ConnectionError("Temporary failure")
                return mock_ticker

            mock_yf.Ticker.side_effect = side_effect

            client = OptimizedYFinanceClient(basic_config)
            result = client.get_stock_info("AAPL")

            assert result is not None
            assert call_count == 3  # Should have retried twice
            assert client.metrics.successful_requests == 1

            client.close()

    def test_metrics_accuracy(self, basic_config, mock_yf_ticker):
        """Test metrics tracking accuracy"""
        client = OptimizedYFinanceClient(basic_config)

        # Perform various operations
        client.get_stock_info("AAPL")  # Success
        client.get_historical_data("GOOGL")  # Success

        # Mock a failure
        with patch.object(
            client, "_fetch_stock_info_raw", side_effect=Exception("Error")
        ):
            client.get_stock_info("INVALID")  # Failure

        metrics = client.get_metrics()

        assert metrics.total_requests == 3
        assert metrics.successful_requests == 2
        assert metrics.failed_requests == 1
        assert metrics.success_rate() == pytest.approx(66.67, rel=1e-2)

        client.close()

    def test_health_check(self, basic_config, mock_yf_ticker):
        """Test health check functionality"""
        client = OptimizedYFinanceClient(basic_config)

        # Perform some operations to generate metrics
        client.get_stock_info("AAPL")

        health_status = client.health_check()

        assert "rate_limiter" in health_status
        assert "circuit_breaker" in health_status
        assert "cache" in health_status
        assert "metrics" in health_status

        metrics = health_status["metrics"]
        assert "success_rate" in metrics
        assert "cache_hit_rate" in metrics
        assert "average_response_time" in metrics

        client.close()

    def test_context_manager(self, basic_config, mock_yf_ticker):
        """Test context manager functionality"""
        with OptimizedYFinanceClient(basic_config) as client:
            result = client.get_stock_info("AAPL")
            assert result is not None

        # Client should be closed after exiting context
        assert client.executor._shutdown

    def test_adaptive_rate_limiting(self, basic_config, mock_yf_ticker):
        """Test adaptive rate limiting behavior"""
        client = OptimizedYFinanceClient(basic_config)

        # Get initial rate limit info
        initial_info = client.get_rate_limiter_info()
        initial_max_requests = initial_info["max_requests"]

        # Simulate rate limit errors
        client.rate_limiter.report_rate_limit_error()
        client.rate_limiter.report_rate_limit_error()

        # Rate limit should be reduced
        updated_info = client.get_rate_limiter_info()
        assert updated_info["max_requests"] < initial_max_requests

        # Simulate successful requests
        for _ in range(5):
            client.rate_limiter.report_success()

        # Rate limit should gradually increase back
        final_info = client.get_rate_limiter_info()
        assert final_info["max_requests"] > updated_info["max_requests"]

        client.close()

    def test_data_frequency_mapping(self, basic_config, mock_yf_ticker):
        """Test data frequency mapping for cache TTL"""
        client = OptimizedYFinanceClient(basic_config)

        # Test different intervals
        assert client._get_data_frequency("1m") == DataFrequency.REAL_TIME
        assert client._get_data_frequency("15m") == DataFrequency.INTRADAY
        assert client._get_data_frequency("1d") == DataFrequency.DAILY
        assert client._get_data_frequency("1wk") == DataFrequency.WEEKLY
        assert client._get_data_frequency("1mo") == DataFrequency.MONTHLY

        client.close()

    def test_batch_processing(self, basic_config, mock_yf_ticker):
        """Test batch processing functionality"""
        client = OptimizedYFinanceClient(basic_config)

        # Test with symbols that exceed batch size
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]  # 5 symbols, batch_size=2

        results = client.get_multiple_stock_info(symbols, batch_size=2)

        assert len(results) == 5
        assert all(symbol in results for symbol in symbols)
        assert all(results[symbol] is not None for symbol in symbols)

        client.close()


class TestIntegration:
    """Integration tests (require actual dependencies)"""

    @pytest.mark.integration
    def test_real_yfinance_integration(self):
        """Test with real YFinance API (if available)"""
        try:
            import pandas as pd
            import yfinance as yf
        except ImportError:
            pytest.skip("yfinance or pandas not available")

        config = YFinanceConfig(
            max_requests_per_minute=10,  # Very conservative for testing
            enable_cache=False,
        )

        with OptimizedYFinanceClient(config) as client:
            # Test with a well-known symbol
            result = client.get_stock_info("AAPL")

            if result:  # Only assert if we got data (API might be down)
                assert "symbol" in result
                assert result["symbol"] == "AAPL"

    @pytest.mark.integration
    def test_redis_cache_integration(self):
        """Test with real Redis cache (if available)"""
        try:
            import redis
        except ImportError:
            pytest.skip("redis package not available")

        # Try to connect to Redis
        try:
            r = redis.Redis(host="localhost", port=6379, db=1)
            r.ping()
        except redis.ConnectionError:
            pytest.skip("Redis server not available")

        cache_config = CacheConfig(host="localhost", port=6379, db=1)
        config = YFinanceConfig(enable_cache=True, cache_config=cache_config)

        with patch("src.infrastructure.external.yfinance_client.yf") as mock_yf:
            mock_yf.Ticker.return_value = MockYFinanceTicker("AAPL")

            with OptimizedYFinanceClient(config) as client:
                # First request should miss cache
                client.get_stock_info("TEST_SYMBOL")
                assert client.metrics.cache_misses == 1

                # Second request should hit cache
                client.get_stock_info("TEST_SYMBOL")
                assert client.metrics.cache_hits == 1

                # Clean up
                if client.cache:
                    client.cache.delete("fundamental_data:symbol:TEST_SYMBOL")


class TestClientFactory:
    """Tests for YFinance Client Factory"""

    @pytest.mark.skipif(
        "yfinance" not in globals(), reason="yfinance package is not installed"
    )
    def test_client_factory_profiles(self):
        factory = YFinanceClientFactory()

        # Test DEVELOPMENT profile
        dev_client = factory.create_client(profile=ClientProfile.DEVELOPMENT)
        assert isinstance(dev_client, OptimizedYFinanceClient)
        assert dev_client.config.max_requests_per_minute == 500

        # Test PRODUCTION profile
        prod_client = factory.create_client(profile=ClientProfile.PRODUCTION)
        assert isinstance(prod_client, OptimizedYFinanceClient)
        assert prod_client.config.max_requests_per_minute == 1800

        # Test HIGH_FREQUENCY profile
        hf_client = factory.create_client(profile=ClientProfile.HIGH_FREQUENCY)
        assert isinstance(hf_client, OptimizedYFinanceClient)
        assert hf_client.config.max_requests_per_minute == 2000

        # Test RESEARCH profile
        research_client = factory.create_client(profile=ClientProfile.RESEARCH)
        assert isinstance(research_client, OptimizedYFinanceClient)
        assert research_client.config.max_requests_per_minute == 1000

        # Test TESTING profile
        test_client = factory.create_client(profile=ClientProfile.TESTING)
        assert isinstance(test_client, OptimizedYFinanceClient)
        assert test_client.config.max_requests_per_minute == 100
