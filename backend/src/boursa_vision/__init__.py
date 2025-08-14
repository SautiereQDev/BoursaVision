"""
Boursa Vision - Advanced Investment Analysis Platform

A comprehensive financial analysis platform providing real-time market data,
investment recommendations, and portfolio management tools.
"""

__version__ = "2.0.0"
__author__ = "Boursa Vision Team"
__email__ = "contact@boursa-vision.com"

# Core exports
from .core.config import get_settings
from .core.exceptions import BoursaVisionError

__all__ = [
    "get_settings",
    "BoursaVisionError",
]
