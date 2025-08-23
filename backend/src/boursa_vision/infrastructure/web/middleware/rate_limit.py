"""
Rate limiting middleware
"""

import asyncio
import time

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using in-memory storage."""

    def __init__(self, app, calls: int = 100, period: int = 60):
        """Initialize rate limiter.

        Args:
            app: FastAPI application
            calls: Number of calls allowed per period
            period: Time period in seconds
        """
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients: dict[str, tuple[int, float]] = {}
        self._lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next) -> Response:
        """Check rate limit and process request."""
        client_ip = self._get_client_ip(request)

        async with self._lock:
            current_time = time.time()

            if client_ip in self.clients:
                calls_count, first_call_time = self.clients[client_ip]

                # Reset counter if period has passed
                if current_time - first_call_time > self.period:
                    self.clients[client_ip] = (1, current_time)
                else:
                    # Check if limit exceeded
                    if calls_count >= self.calls:
                        raise HTTPException(
                            status_code=429,
                            detail="Rate limit exceeded. Try again later.",
                            headers={
                                "Retry-After": str(
                                    int(self.period - (current_time - first_call_time))
                                )
                            },
                        )

                    # Increment counter
                    self.clients[client_ip] = (calls_count + 1, first_call_time)
            else:
                # First call from this client
                self.clients[client_ip] = (1, current_time)

        response = await call_next(request)

        # Add rate limit headers
        if client_ip in self.clients:
            calls_count, first_call_time = self.clients[client_ip]
            remaining = max(0, self.calls - calls_count)
            reset_time = int(first_call_time + self.period)

            response.headers["X-RateLimit-Limit"] = str(self.calls)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded headers (proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to client host
        return request.client.host if request.client else "unknown"
