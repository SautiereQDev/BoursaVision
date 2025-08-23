"""Analyze portfolio query module."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from ...common import IQuery


@dataclass(frozen=True)
class AnalyzePortfolioQuery(IQuery):
    """Query to analyze portfolio performance and risk"""

    portfolio_id: UUID
    benchmark_symbol: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    include_technical_analysis: bool = True
