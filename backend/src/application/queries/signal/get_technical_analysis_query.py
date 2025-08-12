"""Get technical analysis query module."""

from dataclasses import dataclass

from ...common import IQuery


@dataclass(frozen=True)
class GetTechnicalAnalysisQuery(IQuery):
    """Query to get technical analysis for an investment"""

    symbol: str
    period: int = 252  # Trading days for analysis
