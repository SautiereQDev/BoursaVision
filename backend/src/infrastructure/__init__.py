"""
Infrastructure package for Boursa Vision application.

Contains adapters and infrastructure details:
    persistence: Database models and session management.
    web: API endpoints, dependencies, and middleware.
"""

# Import only what's needed to avoid circular imports
from .web import dependencies, main, middleware, routers

__all__ = [
    "dependencies",
    "main",
    "middleware",
    "routers",
]
