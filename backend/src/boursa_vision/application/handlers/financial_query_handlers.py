"""
Financial Query Handlers Implementation
======================================

Handlers for processing financial analytics queries following CQRS pattern.
Integrates with domain services and repositories for comprehensive portfolio analytics.
"""
from decimal import Decimal
from typing import Any

from boursa_vision.domain.repositories import IMarketDataRepository, IPortfolioRepository
from boursa_vision.domain.services.performance_analysis_service import PerformanceAnalysisService
from boursa_vision.domain.services.portfolio_valuation_service import PortfolioValuationService

from ..common import IQueryHandler
from ..queries.portfolio.financial_queries import (
    GetPortfolioAllocationQuery,
    GetPortfolioComparisonQuery,
    GetPortfolioPerformanceQuery,
    GetPortfolioPositionsQuery,
    GetPortfolioRebalancingAnalysisQuery,
    GetPortfolioRiskAnalysisQuery,
    GetPortfolioSummaryQuery,
    GetPortfolioTransactionHistoryQuery,
    GetPortfolioValuationQuery,
    GetUserPortfolioAnalyticsQuery,
)


class GetPortfolioPerformanceQueryHandler(
    IQueryHandler[GetPortfolioPerformanceQuery, dict[str, Any]]
):
    """Handler for portfolio performance analysis query"""

    def __init__(
        self,
        portfolio_repository: IPortfolioRepository,
        market_data_repository: IMarketDataRepository,
    ):
        self._performance_service = PerformanceAnalysisService(
            portfolio_repository, market_data_repository
        )

    async def handle(self, query: GetPortfolioPerformanceQuery) -> dict[str, Any]:
        """
        Handle portfolio performance query.

        Returns comprehensive performance metrics including returns,
        volatility, Sharpe ratio, and position attribution.
        """
        performance_summary = await self._performance_service.generate_performance_summary(
            query.portfolio_id
        )

        result = {
            "portfolio_id": str(query.portfolio_id),
            "performance_summary": performance_summary,
        }

        if query.include_positions:
            attribution = await self._performance_service.calculate_position_attribution(
                query.portfolio_id
            )
            result["position_attribution"] = attribution

        if query.include_historical and query.date_from and query.date_to:
            # Would implement historical performance analysis
            result["historical_performance"] = {
                "period": f"{query.date_from} to {query.date_to}",
                "daily_returns": [],  # Would be populated from historical data
            }

        return result


class GetPortfolioSummaryQueryHandler(
    IQueryHandler[GetPortfolioSummaryQuery, dict[str, Any]]
):
    """Handler for portfolio financial summary query"""

    def __init__(
        self,
        portfolio_repository: IPortfolioRepository,
        market_data_repository: IMarketDataRepository,
    ):
        self._portfolio_repository = portfolio_repository
        self._valuation_service = PortfolioValuationService(
            portfolio_repository, market_data_repository
        )

    async def handle(self, query: GetPortfolioSummaryQuery) -> dict[str, Any]:
        """
        Handle portfolio summary query.

        Returns key financial metrics and portfolio overview.
        """
        portfolio = await self._portfolio_repository.find_by_id(query.portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {query.portfolio_id} not found")

        # Get current portfolio value
        current_value = await self._valuation_service.calculate_portfolio_value(
            query.portfolio_id,
            use_market_prices=True,
            include_cash=True,
        )

        result = {
            "portfolio_id": str(query.portfolio_id),
            "name": portfolio.name,
            "base_currency": portfolio.base_currency,
            "current_value": {
                "amount": str(current_value.amount),
                "currency": portfolio.base_currency,
            },
            "cash_balance": {
                "amount": str(portfolio.cash_balance.amount),
                "currency": portfolio.base_currency,
            },
            "created_at": portfolio.created_at.isoformat(),
        }

        if query.calculate_unrealized_pnl:
            unrealized_pnl = await self._valuation_service.calculate_unrealized_pnl(
                query.portfolio_id
            )
            result["unrealized_pnl"] = str(unrealized_pnl)

        if query.include_position_count:
            result["positions_count"] = len(portfolio._positions)
            result["active_symbols"] = list(portfolio._positions.keys())

        return result


class GetPortfolioValuationQueryHandler(
    IQueryHandler[GetPortfolioValuationQuery, dict[str, Any]]
):
    """Handler for real-time portfolio valuation query"""

    def __init__(
        self,
        portfolio_repository: IPortfolioRepository,
        market_data_repository: IMarketDataRepository,
    ):
        self._valuation_service = PortfolioValuationService(
            portfolio_repository, market_data_repository
        )

    async def handle(self, query: GetPortfolioValuationQuery) -> dict[str, Any]:
        """
        Handle portfolio valuation query.

        Returns real-time portfolio valuation with breakdown.
        """
        portfolio_value = await self._valuation_service.calculate_portfolio_value(
            query.portfolio_id,
            use_market_prices=query.use_market_prices,
            include_cash=query.include_cash,
        )

        result = {
            "portfolio_id": str(query.portfolio_id),
            "total_value": {
                "amount": str(portfolio_value.amount),
                "currency": str(portfolio_value.currency),
            },
            "valuation_timestamp": "now",  # Would use current timestamp
            "use_market_prices": query.use_market_prices,
        }

        if query.include_breakdown:
            breakdown = await self._valuation_service.calculate_positions_breakdown(
                query.portfolio_id, query.use_market_prices
            )
            result["positions_breakdown"] = {
                symbol: {
                    "quantity": str(data["quantity"]),
                    "market_value": str(data["market_value"]),
                    "cost_basis": str(data["cost_basis"]),
                    "unrealized_pnl": str(data["unrealized_pnl"]),
                    "weight_percent": str(data["weight_percent"]),
                }
                for symbol, data in breakdown.items()
            }

        return result


class GetUserPortfolioAnalyticsQueryHandler(
    IQueryHandler[GetUserPortfolioAnalyticsQuery, dict[str, Any]]
):
    """Handler for comprehensive user portfolio analytics query"""

    def __init__(
        self,
        portfolio_repository: IPortfolioRepository,
        market_data_repository: IMarketDataRepository,
    ):
        self._portfolio_repository = portfolio_repository
        self._valuation_service = PortfolioValuationService(
            portfolio_repository, market_data_repository
        )
        self._performance_service = PerformanceAnalysisService(
            portfolio_repository, market_data_repository
        )

    async def handle(self, query: GetUserPortfolioAnalyticsQuery) -> dict[str, Any]:
        """
        Handle user portfolio analytics query.

        Returns comprehensive analytics across all user portfolios.
        """
        # Get all user portfolios
        portfolios = await self._portfolio_repository.find_by_user_id(query.user_id)

        result = {
            "user_id": str(query.user_id),
            "total_portfolios": len(portfolios),
            "analytics_timestamp": "now",  # Would use current timestamp
        }

        if query.include_aggregate_metrics:
            # Calculate aggregate metrics across all portfolios
            total_value = Decimal("0")
            total_cash = Decimal("0")
            
            for portfolio in portfolios:
                portfolio_value = await self._valuation_service.calculate_portfolio_value(
                    portfolio.id, use_market_prices=True, include_cash=True
                )
                total_value += portfolio_value.amount
                total_cash += portfolio.cash_balance.amount

            result["aggregate_metrics"] = {
                "total_value": str(total_value),
                "total_cash": str(total_cash),
                "total_invested": str(total_value - total_cash),
            }

        if query.include_individual_portfolios:
            portfolio_summaries = []
            for portfolio in portfolios:
                summary_query = GetPortfolioSummaryQuery(
                    portfolio_id=portfolio.id,
                    calculate_unrealized_pnl=True,
                    include_position_count=True,
                )
                summary_handler = GetPortfolioSummaryQueryHandler(
                    self._portfolio_repository, None  # Would pass market_data_repository
                )
                summary = await summary_handler.handle(summary_query)
                portfolio_summaries.append(summary)

            result["portfolios"] = portfolio_summaries

        if query.include_performance_comparison and len(portfolios) > 1:
            portfolio_ids = [p.id for p in portfolios]
            comparison = await self._performance_service.compare_portfolios(
                portfolio_ids, period_days=90
            )
            result["performance_comparison"] = comparison

        return result


class GetPortfolioPositionsQueryHandler(
    IQueryHandler[GetPortfolioPositionsQuery, dict[str, Any]]
):
    """Handler for detailed portfolio positions query"""

    def __init__(
        self,
        portfolio_repository: IPortfolioRepository,
        market_data_repository: IMarketDataRepository,
    ):
        self._portfolio_repository = portfolio_repository
        self._valuation_service = PortfolioValuationService(
            portfolio_repository, market_data_repository
        )

    async def handle(self, query: GetPortfolioPositionsQuery) -> dict[str, Any]:
        """
        Handle portfolio positions query.

        Returns detailed information about all portfolio positions.
        """
        portfolio = await self._portfolio_repository.find_by_id(query.portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {query.portfolio_id} not found")

        breakdown = await self._valuation_service.calculate_positions_breakdown(
            query.portfolio_id, use_market_prices=True
        )

        positions = []
        for symbol, data in breakdown.items():
            position_info = {
                "symbol": symbol,
                "quantity": str(data["quantity"]),
                "market_value": str(data["market_value"]),
                "cost_basis": str(data["cost_basis"]),
                "unrealized_pnl": str(data["unrealized_pnl"]),
                "weight_percent": str(data["weight_percent"]),
                "status": "active",  # Would determine from position data
            }
            positions.append(position_info)

        # Sort positions based on query parameters
        if query.sort_by == "market_value":
            positions.sort(
                key=lambda x: float(x["market_value"]), reverse=query.sort_desc
            )
        elif query.sort_by == "pnl":
            positions.sort(
                key=lambda x: float(x["unrealized_pnl"]), reverse=query.sort_desc
            )
        elif query.sort_by == "symbol":
            positions.sort(key=lambda x: x["symbol"], reverse=query.sort_desc)

        return {
            "portfolio_id": str(query.portfolio_id),
            "positions": positions,
            "total_positions": len(positions),
            "sort_by": query.sort_by,
            "sort_desc": query.sort_desc,
        }
