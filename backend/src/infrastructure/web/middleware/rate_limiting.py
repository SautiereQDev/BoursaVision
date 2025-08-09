"""Rate limiting middleware placeholder."""


class RateLimitMiddleware:
    """Placeholder rate limiting middleware."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        # Placeholder implementation
        await self.app(scope, receive, send)
