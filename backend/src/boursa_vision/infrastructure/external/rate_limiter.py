"""
Rate Limiter Implementation
===========================

Sliding window rate limiter for API requests.
"""

import time
from collections import deque
from dataclasses import dataclass
from threading import Lock


@dataclass
class RateLimit:
    """Rate limit configuration"""

    max_requests: int
    window_seconds: int


class SlidingWindowRateLimiter:
    """
    Limiteur de débit basé sur une fenêtre glissante, sécurisé pour les threads.

    Attributes:
        rate_limit: Configuration du débit maximal autorisé.
        _request_times: File contenant les timestamps des requêtes récentes.
        _lock: Verrou pour garantir la sécurité des threads.

    Methods:
        can_proceed: Vérifie si une requête peut être effectuée sans dépasser les limites.
        _cleanup_old_requests: Supprime les requêtes obsolètes de la file.
    """

    def __init__(self, rate_limit: RateLimit):
        self.rate_limit = rate_limit
        self._request_times: deque = deque()
        self._lock = Lock()

    def can_proceed(self) -> bool:
        """Check if a request can proceed without violating rate limits."""
        with self._lock:
            current_time = time.time()
            self._cleanup_old_requests(current_time)
            return len(self._request_times) < self.rate_limit.max_requests

    def acquire(self) -> bool:
        """
        Attempt to acquire a permit for a request.

        Returns:
            True if the request can proceed, False if rate limited.
        """
        with self._lock:
            current_time = time.time()
            self._cleanup_old_requests(current_time)

            if len(self._request_times) < self.rate_limit.max_requests:
                self._request_times.append(current_time)
                return True
            return False

    def wait_time_until_available(self) -> float:
        """
        Calculate the time to wait until a request slot becomes available.

        Returns:
            Time in seconds to wait, or 0 if immediately available.
        """
        with self._lock:
            current_time = time.time()
            self._cleanup_old_requests(current_time)

            if len(self._request_times) < self.rate_limit.max_requests:
                return 0.0

            # Time until the oldest request expires
            oldest_request = self._request_times[0]
            return oldest_request + self.rate_limit.window_seconds - current_time

    def _cleanup_old_requests(self, current_time: float) -> None:
        """Remove requests outside the time window."""
        cutoff_time = current_time - self.rate_limit.window_seconds
        while self._request_times and self._request_times[0] <= cutoff_time:
            self._request_times.popleft()

    def get_current_usage(self) -> int:
        """Get current number of requests in the window."""
        with self._lock:
            self._cleanup_old_requests(time.time())
            return len(self._request_times)


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter that adjusts based on API responses.

    Implements the Adapter pattern to work with different rate limiting strategies.
    """

    def __init__(self, base_rate_limit: RateLimit):
        self.base_rate_limit = base_rate_limit
        self.current_rate_limit = base_rate_limit
        self.limiter = SlidingWindowRateLimiter(base_rate_limit)
        self._consecutive_errors = 0
        self._lock = Lock()

    def can_proceed(self) -> bool:
        """Check if a request can proceed."""
        return self.limiter.can_proceed()

    def acquire(self) -> bool:
        """Acquire a permit for a request."""
        return self.limiter.acquire()

    def wait_time_until_available(self) -> float:
        """Get wait time until next request is allowed."""
        return self.limiter.wait_time_until_available()

    def report_success(self) -> None:
        """Report a successful request to potentially increase rate limit."""
        with self._lock:
            self._consecutive_errors = 0
            # Gradually increase rate limit back to base if it was reduced
            if self.current_rate_limit.max_requests < self.base_rate_limit.max_requests:
                new_limit = min(
                    self.current_rate_limit.max_requests + 1,
                    self.base_rate_limit.max_requests,
                )
                self._update_rate_limit(new_limit)

    def report_rate_limit_error(self) -> None:
        """Report a rate limit error to reduce future requests."""
        with self._lock:
            self._consecutive_errors += 1
            # Reduce rate limit by 10% after rate limit errors
            reduction_factor = 0.9
            new_limit = max(
                int(self.current_rate_limit.max_requests * reduction_factor),
                1,  # Never go below 1 request
            )
            self._update_rate_limit(new_limit)

    def _update_rate_limit(self, new_max_requests: int) -> None:
        """Update the rate limit and create a new limiter."""
        self.current_rate_limit = RateLimit(
            max_requests=new_max_requests,
            window_seconds=self.current_rate_limit.window_seconds,
        )
        self.limiter = SlidingWindowRateLimiter(self.current_rate_limit)

    def get_current_usage(self) -> int:
        """Get current usage statistics."""
        return self.limiter.get_current_usage()

    def get_rate_limit_info(self) -> dict[str, int]:
        """Get current rate limit information."""
        return {
            "max_requests": self.current_rate_limit.max_requests,
            "window_seconds": self.current_rate_limit.window_seconds,
            "current_usage": self.get_current_usage(),
            "consecutive_errors": self._consecutive_errors,
        }
