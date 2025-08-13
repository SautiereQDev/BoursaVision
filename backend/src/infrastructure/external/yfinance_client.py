"""
YFinance Client Implementation
=============================

Optimized YFinance client with rate limiting, caching, and resilience patterns.
"""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import yfinance as yf
except ImportError:
    yf = None

from .cache_strategy import (
    AdaptiveCacheStrategy,
    CacheConfig,
    CacheKeyBuilder,
    DataFrequency,
    RedisCache,
)
from .circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from .rate_limiter import AdaptiveRateLimiter, RateLimit
from .retry_strategy import (
    RateLimitError,
    RetryConfig,
    RetryHandler,
    TemporaryFailureError,
)

logger = logging.getLogger(__name__)


@dataclass
class YFinanceConfig:
    """YFinance client configuration"""

    # Rate limiting
    max_requests_per_minute: int = 2000
    rate_limit_window: int = 60

    # Concurrency
    max_concurrent_requests: int = 50
    batch_size: int = 10

    # Timeouts
    request_timeout: float = 30.0

    # Retry configuration
    max_retries: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 60.0

    # Circuit breaker
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: float = 60.0

    # Cache
    enable_cache: bool = True
    cache_config: Optional[CacheConfig] = None


@dataclass
class RequestMetrics:
    """Metrics for monitoring API usage"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    rate_limit_errors: int = 0
    circuit_breaker_trips: int = 0
    average_response_time: float = 0.0

    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage"""
        total_cache_requests = self.cache_hits + self.cache_misses
        if total_cache_requests == 0:
            return 0.0
        return (self.cache_hits / total_cache_requests) * 100


class YFinanceError(Exception):
    """Base exception for YFinance client errors"""

    pass


class YFinanceRateLimitError(YFinanceError):
    """Raised when rate limit is exceeded"""

    pass


class YFinanceTimeoutError(YFinanceError):
    """Raised when request times out"""

    pass


class OptimizedYFinanceClient:
    """
    Optimized YFinance client with rate limiting, caching, and resilience.

    Attributes:
        config: Configuration for the YFinance client.
        metrics: Metrics for monitoring API usage and performance.
        rate_limiter: Rate limiter to ensure API quota compliance.
        circuit_breaker: Circuit breaker to prevent cascading failures.
        retry_handler: Retry handler for temporary errors.
        cache: Redis cache for frequently accessed data.
        executor: Thread pool for parallel requests.

    Methods:
        get_stock_info: Fetches stock information for a single symbol.
        get_multiple_stock_info: Fetches stock information for multiple symbols in parallel.
        health_check: Checks the health of the client's components.
    """

    def __init__(self, config: YFinanceConfig):
        if yf is None:
            raise ImportError(
                "yfinance package is required. Install with: pip install yfinance"
            )

        self.config = config
        self.metrics = RequestMetrics()

        # Initialize components
        self._init_rate_limiter()
        self._init_circuit_breaker()
        self._init_retry_handler()
        self._init_cache()

        # Thread pool for concurrent requests
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_requests)

        logger.info("OptimizedYFinanceClient initialized successfully")

    def _init_rate_limiter(self) -> None:
        """Initialize rate limiter"""
        rate_limit = RateLimit(
            max_requests=self.config.max_requests_per_minute,
            window_seconds=self.config.rate_limit_window,
        )
        self.rate_limiter = AdaptiveRateLimiter(rate_limit)

    def _init_circuit_breaker(self) -> None:
        """Initialize circuit breaker"""
        cb_config = CircuitBreakerConfig(
            failure_threshold=self.config.circuit_breaker_failure_threshold,
            recovery_timeout=self.config.circuit_breaker_recovery_timeout,
            timeout=self.config.request_timeout,
        )
        self.circuit_breaker = CircuitBreaker(cb_config)

    def _init_retry_handler(self) -> None:
        """Initialize retry handler"""
        retry_config = RetryConfig(
            max_attempts=self.config.max_retries,
            base_delay=self.config.retry_base_delay,
            max_delay=self.config.retry_max_delay,
        )
        self.retry_handler = RetryHandler(retry_config)

    def _init_cache(self) -> None:
        """Initialize cache if enabled"""
        if self.config.enable_cache:
            cache_config = self.config.cache_config or CacheConfig()
            cache_strategy = AdaptiveCacheStrategy(cache_config)
            self.cache = RedisCache(cache_config, cache_strategy)
        else:
            self.cache = None

    def get_stock_info(
        self, symbol: str, use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Get stock information for a single symbol.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            use_cache: Whether to use cache

        Returns:
            Stock information dictionary or None if failed
        """
        cache_key = CacheKeyBuilder.for_fundamental_data(symbol)

        # Try cache first
        if use_cache and self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self.metrics.cache_hits += 1
                return cached_data
            self.metrics.cache_misses += 1

        # Fetch from API
        try:
            start_time = time.time()

            def fetch_info():
                return self._fetch_stock_info_with_resilience(symbol)

            result = self.retry_handler.execute(fetch_info)

            # Update metrics
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            self.metrics.successful_requests += 1

            # Cache result
            if result and use_cache and self.cache:
                self.cache.set(cache_key, result, DataFrequency.DAILY)

            return result

        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error("Failed to get stock info for %s: %s", symbol, e)
            return None
        finally:
            self.metrics.total_requests += 1

    def get_historical_data(
        self,
        symbol: str,
        period: str = "1y",
        interval: str = "1d",
        use_cache: bool = True,
    ) -> Optional[Any]:
        """
        Get historical price data for a symbol.

        Args:
            symbol: Stock symbol
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            use_cache: Whether to use cache

        Returns:
            Historical data DataFrame or None if failed
        """
        cache_key = CacheKeyBuilder.for_price_data(symbol, period, interval)

        # Determine data frequency for cache TTL
        frequency = self._get_data_frequency(interval)

        # Try cache first
        if use_cache and self.cache:
            cached_data = self.cache.get(cache_key)
            if cached_data:
                self.metrics.cache_hits += 1
                return cached_data
            self.metrics.cache_misses += 1

        # Fetch from API
        try:
            start_time = time.time()

            def fetch_data():
                return self._fetch_historical_data_with_resilience(
                    symbol, period, interval
                )

            result = self.retry_handler.execute(fetch_data)

            # Update metrics
            response_time = time.time() - start_time
            self._update_response_time(response_time)
            self.metrics.successful_requests += 1

            # Cache result
            if result is not None and use_cache and self.cache:
                # Convert DataFrame to dict for caching
                if hasattr(result, "to_dict"):
                    cache_data = result.to_dict("records")
                else:
                    cache_data = result
                self.cache.set(cache_key, cache_data, frequency)

            return result

        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error("Failed to get historical data for %s: %s", symbol, e)
            return None
        finally:
            self.metrics.total_requests += 1

    def get_multiple_stock_info(
        self,
        symbols: List[str],
        use_cache: bool = True,
        batch_size: Optional[int] = None,
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Get stock information for multiple symbols in parallel.

        Args:
            symbols: List of stock symbols
            use_cache: Whether to use cache
            batch_size: Batch size for parallel processing

        Returns:
            Dictionary mapping symbols to their info
        """
        if not symbols:
            return {}

        batch_size = batch_size or self.config.batch_size
        results = {}

        # Process symbols in batches
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]
            batch_results = self._process_batch_parallel(
                batch, lambda symbol: self.get_stock_info(symbol, use_cache)
            )
            results.update(batch_results)

        return results

    def get_multiple_historical_data(
        self,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Get historical data for multiple symbols in parallel.

        Args:
            config: Configuration dictionary with keys:
                - symbols: List of stock symbols
                - period: Data period
                - interval: Data interval
                - use_cache: Whether to use cache
                - batch_size: Batch size for parallel processing

        Returns:
            Dictionary mapping symbols to their historical data
        """
        symbols = config.get("symbols", [])
        period = config.get("period", "1y")
        interval = config.get("interval", "1d")
        use_cache = config.get("use_cache", True)
        batch_size = config.get("batch_size", self.config.batch_size)

        if not symbols:
            return {}

        results = {}

        # Process symbols in batches
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i : i + batch_size]
            batch_results = self._process_batch_parallel(
                batch,
                lambda symbol: self.get_historical_data(
                    symbol, period, interval, use_cache
                ),
            )
            results.update(batch_results)

        return results

    def _process_batch_parallel(self, symbols: List[str], fetch_func) -> Dict[str, Any]:
        """Process a batch of symbols in parallel"""
        results = {}

        # Submit all tasks
        future_to_symbol = {
            self.executor.submit(fetch_func, symbol): symbol for symbol in symbols
        }

        # Collect results as they complete
        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                result = future.result(timeout=self.config.request_timeout)
                results[symbol] = result
            except Exception as e:
                logger.error("Error processing %s: %s", symbol, e)
                results[symbol] = None

        return results

    def _fetch_stock_info_with_resilience(
        self, symbol: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch stock info with rate limiting and circuit breaker"""
        return self.circuit_breaker.call(self._fetch_stock_info_raw, symbol)

    def _fetch_historical_data_with_resilience(
        self, symbol: str, period: str, interval: str
    ) -> Optional[Any]:
        """Fetch historical data with rate limiting and circuit breaker"""
        return self.circuit_breaker.call(
            self._fetch_historical_data_raw, symbol, period, interval
        )

    def _fetch_stock_info_raw(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Raw fetch stock info with rate limiting"""
        if not self.rate_limiter.acquire():
            wait_time = self.rate_limiter.wait_time_until_available()
            if wait_time > 0:
                time.sleep(wait_time)
                if not self.rate_limiter.acquire():
                    self.metrics.rate_limit_errors += 1
                    raise RateLimitError(f"Rate limit exceeded for {symbol}")

        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            self.rate_limiter.report_success()
            return info

        except RateLimitError as e:
            self.rate_limiter.report_rate_limit_error()
            raise RateLimitError(f"Rate limit error for {symbol}: {e}") from e

        except TemporaryFailureError as e:
            self.rate_limiter.report_rate_limit_error()
            raise TemporaryFailureError(
                f"Failed to fetch info for {symbol}: {e}"
            ) from e

        except Exception as e:
            logger.error("Unexpected error: %s", e)
            raise

    def _fetch_historical_data_raw(
        self, symbol: str, period: str, interval: str
    ) -> Optional[Any]:
        """Raw fetch historical data with rate limiting"""
        if not self.rate_limiter.acquire():
            wait_time = self.rate_limiter.wait_time_until_available()
            if wait_time > 0:
                time.sleep(wait_time)
                if not self.rate_limiter.acquire():
                    self.metrics.rate_limit_errors += 1
                    raise RateLimitError(f"Rate limit exceeded for {symbol}")

        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period, interval=interval)
            self.rate_limiter.report_success()
            return data

        except RateLimitError as e:
            self.rate_limiter.report_rate_limit_error()
            raise RateLimitError(f"Rate limit error for {symbol}: {e}") from e

        except TemporaryFailureError as e:
            self.rate_limiter.report_rate_limit_error()
            raise TemporaryFailureError(
                f"Failed to fetch data for {symbol}: {e}"
            ) from e

        except Exception as e:
            logger.error("Unexpected error: %s", e)
            raise

    def _get_data_frequency(self, interval: str) -> DataFrequency:
        """Determine data frequency based on interval"""
        if interval in ["1m", "2m", "5m"]:
            return DataFrequency.REAL_TIME
        if interval in ["15m", "30m", "60m", "90m", "1h"]:
            return DataFrequency.INTRADAY
        if interval in ["1d"]:
            return DataFrequency.DAILY
        if interval in ["5d", "1wk"]:
            return DataFrequency.WEEKLY
        return DataFrequency.MONTHLY

    def _update_response_time(self, response_time: float) -> None:
        """Update average response time"""
        if self.metrics.successful_requests == 1:
            self.metrics.average_response_time = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.average_response_time = (
                alpha * response_time + (1 - alpha) * self.metrics.average_response_time
            )

    def get_metrics(self) -> RequestMetrics:
        """Get current metrics"""
        return self.metrics

    def get_rate_limiter_info(self) -> Dict[str, Any]:
        """Get rate limiter information"""
        return self.rate_limiter.get_rate_limit_info()

    def get_circuit_breaker_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        return self.circuit_breaker.get_stats()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if self.cache:
            return self.cache.get_stats()
        return {"status": "disabled"}

    def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        return {
            "rate_limiter": self.get_rate_limiter_info(),
            "circuit_breaker": self.get_circuit_breaker_stats(),
            "cache": self.get_cache_stats(),
            "metrics": {
                "success_rate": self.metrics.success_rate(),
                "cache_hit_rate": self.metrics.cache_hit_rate(),
                "average_response_time": self.metrics.average_response_time,
            },
        }

    def reset_metrics(self) -> None:
        """Reset all metrics"""
        self.metrics = RequestMetrics()

    def close(self) -> None:
        """Clean up resources"""
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=True)
        logger.info("OptimizedYFinanceClient closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
