"""
Investment Queries - Complete Schema Support
===========================================

Advanced queries for investment analysis leveraging the complete
position and financial schema for detailed investment tracking.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from boursa_vision.application.common import IQuery


@dataclass(frozen=True)
class GetInvestmentPositionsQuery(IQuery):
    """
    Query to get all investment positions across portfolios.

    Returns detailed position information with P&L calculations
    and performance metrics using the complete position schema.
    """

    investment_id: UUID | None = None
    portfolio_id: UUID | None = None
    symbol: str | None = None
    include_closed_positions: bool = False
    include_performance: bool = True


@dataclass(frozen=True)
class GetInvestmentPerformanceQuery(IQuery):
    """
    Query to get investment performance analysis.

    Analyzes individual investment performance across all positions
    using the complete financial schema for comprehensive metrics.
    """

    investment_id: UUID
    include_historical_data: bool = True
    timeframe_days: int = 90
    include_benchmark_comparison: bool = False


@dataclass(frozen=True)
class GetInvestmentMarketDataQuery(IQuery):
    """
    Query to get current and historical market data for investments.

    Retrieves market data with technical indicators and price analysis
    using the complete market data schema.
    """

    symbol: str | None = None
    investment_id: UUID | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None
    include_indicators: bool = False
    data_interval: str = "1d"  # "1d", "1h", "5m", etc.


@dataclass(frozen=True)
class SearchInvestmentsQuery(IQuery):
    """
    Query to search investments by various criteria.

    Searches investments with filtering and sorting capabilities
    using investment metadata and market data.
    """

    search_term: str | None = None
    sector: str | None = None
    market_cap_min: Decimal | None = None
    market_cap_max: Decimal | None = None
    sort_by: str = "market_cap"
    sort_desc: bool = True
    limit: int = 50


@dataclass(frozen=True)
class GetInvestmentAllocationQuery(IQuery):
    """
    Query to get investment allocation across all portfolios.

    Shows how an investment is allocated across different portfolios
    with total exposure and concentration analysis.
    """

    investment_id: UUID
    include_portfolio_details: bool = True
    include_risk_metrics: bool = False
