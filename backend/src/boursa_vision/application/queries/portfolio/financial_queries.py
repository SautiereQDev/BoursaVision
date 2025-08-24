"""
Portfolio Financial Queries - Complete Schema Support
====================================================

Advanced queries for portfolio financial analysis leveraging the complete
financial schema with comprehensive performance metrics and analytics.
"""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from boursa_vision.application.common import IQuery


@dataclass(frozen=True)
class GetPortfolioPerformanceQuery(IQuery):
    """
    Query to get comprehensive portfolio performance analysis.

    Leverages the complete financial schema to provide detailed performance
    metrics including P&L analysis, return calculations, and position breakdowns.
    """

    portfolio_id: UUID
    include_positions: bool = True
    include_historical: bool = False
    date_from: datetime | None = None
    date_to: datetime | None = None


@dataclass(frozen=True)
class GetPortfolioSummaryQuery(IQuery):
    """
    Query to get portfolio financial summary.
    
    Returns key financial metrics from the complete schema including
    cash balances, total values, P&L figures, and return percentages.
    """
    
    portfolio_id: UUID
    calculate_unrealized_pnl: bool = True
    include_position_count: bool = True


@dataclass(frozen=True)
class GetUserPortfolioAnalyticsQuery(IQuery):
    """
    Query to get comprehensive analytics for all user portfolios.
    
    Aggregates data across all user portfolios using the complete financial
    schema for cross-portfolio analysis and total wealth calculations.
    """
    
    user_id: UUID
    include_individual_portfolios: bool = True
    include_aggregate_metrics: bool = True
    include_performance_comparison: bool = False


@dataclass(frozen=True)
class GetPortfolioPositionsQuery(IQuery):
    """
    Query to get detailed position information for a portfolio.
    
    Returns all positions with market values, P&L calculations, and
    performance metrics using the complete position tracking schema.
    """
    
    portfolio_id: UUID
    include_closed_positions: bool = False
    sort_by: str = "market_value"  # "market_value", "pnl", "symbol", "quantity"
    sort_desc: bool = True


@dataclass(frozen=True)
class GetPortfolioValuationQuery(IQuery):
    """
    Query to get real-time portfolio valuation.
    
    Calculates current portfolio value using live market prices and
    the complete financial schema for accurate portfolio valuation.
    """
    
    portfolio_id: UUID
    use_market_prices: bool = True
    include_cash: bool = True
    include_breakdown: bool = True


@dataclass(frozen=True)
class GetPortfolioRiskAnalysisQuery(IQuery):
    """
    Query to get portfolio risk analysis.
    
    Analyzes portfolio risk metrics including concentration, volatility,
    and diversification using the complete position and financial data.
    """
    
    portfolio_id: UUID
    risk_timeframe_days: int = 30
    include_sector_analysis: bool = True
    include_correlation_analysis: bool = False


@dataclass(frozen=True)
class GetPortfolioComparisonQuery(IQuery):
    """
    Query to compare multiple portfolios.
    
    Compares performance, allocation, and risk metrics across multiple
    portfolios using the complete financial schema for comprehensive analysis.
    """
    
    portfolio_ids: list[UUID]
    comparison_period_days: int = 90
    include_performance_metrics: bool = True
    include_allocation_analysis: bool = True
    include_risk_metrics: bool = False


@dataclass(frozen=True)
class GetPortfolioAllocationQuery(IQuery):
    """
    Query to get portfolio allocation analysis.
    
    Analyzes current portfolio allocation by various dimensions using
    the complete position data and financial schema.
    """
    
    portfolio_id: UUID
    group_by: str = "symbol"  # "symbol", "sector", "market_cap", "region"
    include_target_allocation: bool = False
    show_percentages: bool = True


@dataclass(frozen=True)
class GetPortfolioTransactionHistoryQuery(IQuery):
    """
    Query to get portfolio transaction history with P&L tracking.
    
    Returns historical transactions with realized P&L calculations
    and performance impact analysis using the complete financial schema.
    """
    
    portfolio_id: UUID
    transaction_type: str | None = None  # "buy", "sell", "dividend", "all"
    date_from: datetime | None = None
    date_to: datetime | None = None
    include_pnl_impact: bool = True
    limit: int = 100


@dataclass(frozen=True)
class GetPortfolioRebalancingAnalysisQuery(IQuery):
    """
    Query to analyze portfolio rebalancing opportunities.
    
    Analyzes current vs target allocations and suggests rebalancing
    actions using the complete position and financial data.
    """
    
    portfolio_id: UUID
    target_allocations: dict[str, Decimal] | None = None
    rebalancing_threshold_pct: Decimal = Decimal("5.0")
    include_tax_implications: bool = False
    include_transaction_costs: bool = True
