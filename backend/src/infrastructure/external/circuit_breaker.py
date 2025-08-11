"""
Circuit Breaker Pattern Implementation
======================================

Circuit breaker to prevent cascading failures and provide fail-fast behavior.
"""

import time
from dataclasses import dataclass
from enum import Enum
from threading import Lock
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failing, rejecting requests
    HALF_OPEN = "HALF_OPEN"  # Testing if service is back


@dataclass
class CircuitBreakerConfig:
    """Circuit breaker configuration"""

    failure_threshold: int = 5  # Number of failures before opening
    recovery_timeout: float = 60.0  # Seconds before trying half-open
    success_threshold: int = 3  # Successes needed to close from half-open
    timeout: float = 30.0  # Request timeout in seconds


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is open"""

    ...


class CircuitBreaker:
    """
    Circuit breaker implementation following the Circuit Breaker pattern.

    Attributes:
        config: Configuration for the circuit breaker.
        state: Current state of the circuit (CLOSED, OPEN, HALF_OPEN).
        failure_count: Number of consecutive failures.
        success_count: Number of consecutive successes in HALF_OPEN state.
        lock: Lock to ensure thread safety.

    Methods:
        call: Executes a function protected by the circuit breaker.
        get_state: Returns the current state of the circuit.
        reset: Resets the circuit breaker to its initial state.
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = Lock()

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute a function through the circuit breaker.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            CircuitBreakerError: When circuit is open
            Exception: Original function exceptions when circuit is closed/half-open
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitBreakerError(
                        f"Circuit breaker is OPEN. Last failure: {self.last_failure_time}"
                    )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt a reset."""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.config.recovery_timeout

    def _on_success(self) -> None:
        """Handle successful request."""
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self._reset()
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed request."""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()

            if self.state == CircuitState.HALF_OPEN or (
                self.state == CircuitState.CLOSED
                and self.failure_count >= self.config.failure_threshold
            ):
                self.state = CircuitState.OPEN

    def _reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state."""
        return self.state

    def get_stats(self) -> dict:
        """Get circuit breaker statistics."""
        with self._lock:
            return {
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "last_failure_time": self.last_failure_time,
                "time_since_last_failure": (
                    time.time() - self.last_failure_time
                    if self.last_failure_time
                    else None
                ),
            }

    def force_open(self) -> None:
        """Force circuit breaker to open state (for testing)."""
        with self._lock:
            self.state = CircuitState.OPEN
            self.last_failure_time = time.time()

    def force_close(self) -> None:
        """Force circuit breaker to closed state (for testing)."""
        with self._lock:
            self._reset()


class CircuitBreakerRegistry:
    """
    Registry to manage multiple circuit breakers.

    Implements the Registry pattern for managing circuit breaker instances.
    """

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = Lock()

    def get_or_create(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Get existing circuit breaker or create a new one."""
        with self._lock:
            if name not in self._breakers:
                self._breakers[name] = CircuitBreaker(config)
            return self._breakers[name]

    def get(self, name: str) -> Optional[CircuitBreaker]:
        """
        Retrieve an existing circuit breaker by its name.

        Args:
            name: The name of the circuit breaker.

        Returns:
            CircuitBreaker if found, otherwise None.
        """
        with self._lock:
            return self._breakers.get(name)
