"""
Infrastructure package for Boursa Vision application.

Contains adapters and infrastructure details:
    persistence: Database models and session management.
    web: API endpoints, dependencies, and middleware.
"""

from .persistence import models
from .persistence.sqlalchemy import session
from .web import dependencies, main, middleware, routers

__all__ = [
    "models",
    "session",
    "dependencies",
    "main",
    "middleware",
    "routers",
]
