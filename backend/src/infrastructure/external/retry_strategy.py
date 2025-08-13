"""
Retry Strategy Implementation
============================

Retry mechanisms with exponential backoff and jitter.
"""

import asyncio
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


class RetryCondition(Enum):
    """Conditions that should trigger a retry"""

    TIMEOUT = "TIMEOUT"
    RATE_LIMIT = "RATE_LIMIT"
    SERVER_ERROR = "SERVER_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    TEMPORARY_FAILURE = "TEMPORARY_FAILURE"


@dataclass
class RetryConfig:
    """Retry configuration"""

    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_base: float = 2.0
    jitter: bool = True
    retry_conditions: Optional[set[RetryCondition]] = None

    def __post_init__(self):
        if self.retry_conditions is None:
            self.retry_conditions = {
                RetryCondition.TIMEOUT,
                RetryCondition.RATE_LIMIT,
                RetryCondition.SERVER_ERROR,
                RetryCondition.NETWORK_ERROR,
                RetryCondition.TEMPORARY_FAILURE,
            }


class RetryableError(Exception):
    """Base class for retryable errors"""

    def __init__(self, message: str, condition: RetryCondition):
        super().__init__(message)
        self.condition = condition


class RateLimitError(RetryableError):
    """Raised when rate limit is exceeded"""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, RetryCondition.RATE_LIMIT)


class TemporaryFailureError(RetryableError):
    """Raised for temporary failures that should be retried"""

    def __init__(self, message: str = "Temporary failure"):
        super().__init__(message, RetryCondition.TEMPORARY_FAILURE)


class RetryStrategy(ABC):
    """Abstract base class for retry strategies"""

    @abstractmethod
    def calculate_delay(
        self, attempt: int, base_delay: float, max_delay: float
    ) -> float:
        """Calculate delay for the given attempt number"""
        pass


class ExponentialBackoffStrategy(RetryStrategy):
    """Exponential backoff retry strategy"""

    def __init__(self, exponential_base: float = 2.0, jitter: bool = True):
        self.exponential_base = exponential_base
        self.jitter = jitter

    def calculate_delay(
        self, attempt: int, base_delay: float, max_delay: float
    ) -> float:
        """Calculate exponential backoff delay with optional jitter"""
        delay = base_delay * (self.exponential_base**attempt)
        delay = min(delay, max_delay)

        if self.jitter:
            # Add jitter: random value between 50% and 100% of calculated delay
            jitter_min = delay * 0.5
            delay = random.uniform(jitter_min, delay)

        return delay


class LinearBackoffStrategy(RetryStrategy):
    """Linear backoff retry strategy"""

    def __init__(self, increment: float = 1.0, jitter: bool = True):
        self.increment = increment
        self.jitter = jitter

    def calculate_delay(
        self, attempt: int, base_delay: float, max_delay: float
    ) -> float:
        """Calculate linear backoff delay"""
        delay = base_delay + (self.increment * attempt)
        delay = min(delay, max_delay)

        if self.jitter:
            jitter_range = min(delay * 0.1, 1.0)  # 10% jitter, max 1 second
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0, delay)


class RetryHandler:
    """
    Retry handler with exponential backoff and jitter.

    Attributes:
        config: Configuration for retry parameters.

    Methods:
        execute: Executes a function with retry attempts in case of failure.
        _calculate_delay: Calculates the delay between attempts based on backoff.
    """

    def __init__(self, config: RetryConfig, strategy: Optional[RetryStrategy] = None):
        self.config = config
        self.strategy = strategy or ExponentialBackoffStrategy(
            exponential_base=config.exponential_base, jitter=config.jitter
        )

    def execute(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if not self._should_retry(e, attempt):
                    raise e

                if (
                    attempt < self.config.max_attempts - 1
                ):  # Don't delay after last attempt
                    delay = self.strategy.calculate_delay(
                        attempt, self.config.base_delay, self.config.max_delay
                    )
                    time.sleep(delay)

        # All retries exhausted
        raise last_exception

    async def execute_async(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute async function with retry logic.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: Last exception if all retries exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e

                if not self._should_retry(e, attempt):
                    raise e

                if (
                    attempt < self.config.max_attempts - 1
                ):  # Don't delay after last attempt
                    delay = self.strategy.calculate_delay(
                        attempt, self.config.base_delay, self.config.max_delay
                    )
                    await asyncio.sleep(delay)

        # All retries exhausted
        raise last_exception

    def _should_retry(self, exception: Exception, attempt: int) -> bool:
        """Determine if an exception should trigger a retry"""
        if attempt >= self.config.max_attempts - 1:
            return False

        # Check if it's a known retryable error
        if isinstance(exception, RetryableError):
            return exception.condition in self.config.retry_conditions

        # Check for common retryable exceptions
        if isinstance(exception, (TimeoutError, ConnectionError)):
            return RetryCondition.NETWORK_ERROR in self.config.retry_conditions

        # Add more specific exception handling as needed
        return False


class RetryDecorator:
    """
    Decorator for adding retry behavior to functions.

    Example:
        @RetryDecorator(RetryConfig(max_attempts=3))
        def api_call():
            # Function that might fail
            pass
    """

    def __init__(self, config: RetryConfig, strategy: Optional[RetryStrategy] = None):
        self.handler = RetryHandler(config, strategy)

    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Apply retry logic to function"""
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                return await self.handler.execute_async(func, *args, **kwargs)

            return async_wrapper

        def sync_wrapper(*args, **kwargs):
            return self.handler.execute(func, *args, **kwargs)

        return sync_wrapper


# Convenience decorators
def retry_with_exponential_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
):
    """Decorator for exponential backoff retry"""
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        exponential_base=exponential_base,
        jitter=jitter,
    )
    return RetryDecorator(config, ExponentialBackoffStrategy(exponential_base, jitter))


def retry_on_rate_limit(max_attempts: int = 5, base_delay: float = 2.0):
    """Decorator specifically for rate limit retries"""
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=300.0,  # 5 minutes max
        retry_conditions={RetryCondition.RATE_LIMIT},
    )
    return RetryDecorator(config)
