"""
Boursa Vision - Advanced Investment Analysis Platform

A comprehensive financial analysis platform providing real-time market data,
investment recommendations, and portfolio management tools.
"""

__version__ = "2.0.0"
__author__ = "Boursa Vision Team"
__email__ = "contact@boursa-vision.com"

# Core exports - Import only when needed to avoid circular dependencies
__all__ = [
    "get_settings",
    "BoursaVisionError",
]


def get_settings():
    """Lazy import to avoid dependency issues."""
    from .core.config import get_settings as _get_settings

    return _get_settings()


class BoursaVisionError(Exception):
    """Base exception for Boursa Vision errors."""

    pass
