"""Analyze portfolio query module."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID

from ...common import IQuery


@dataclass(frozen=True)
class AnalyzePortfolioQuery(IQuery):
    """Query to analyze portfolio performance and risk"""

    portfolio_id: UUID
    benchmark_symbol: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_technical_analysis: bool = True
