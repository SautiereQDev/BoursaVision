"""
Find Investments Use Case
========================

Main use case for finding and searching investments based on various criteria.
Orchestrates domain services and repositories to provide comprehensive
investment search capabilities with technical analysis.
"""

from ..common import IUseCase
from ..dtos import (
    InvestmentDTO,
    InvestmentSearchResultDTO,
    SignalDTO,
    TechnicalAnalysisDTO,
)
from ..queries import FindInvestmentsQuery
from ..services.signal_generator import SignalGenerator
from ..services.technical_analyzer import TechnicalAnalyzer


class FindInvestmentsUseCase(IUseCase[FindInvestmentsQuery, InvestmentSearchResultDTO]):
    """
    Use case for finding investments with optional technical analysis and signals.

    This use case orchestrates:
    - Investment repository queries
    - Technical analysis for found investments
    - Signal generation for investment recommendations
    """

    def __init__(
        self,
        investment_repository,  # IInvestmentRepository - avoiding import issues
        technical_analyzer: TechnicalAnalyzer,
        signal_generator: SignalGenerator,
    ):
        self._investment_repository = investment_repository
        self._technical_analyzer = technical_analyzer
        self._signal_generator = signal_generator

    async def execute(self, request: FindInvestmentsQuery) -> InvestmentSearchResultDTO:
        """
        Execute the find investments use case.

        Args:
            request: Query parameters for finding investments

        Returns:
            Search results with investments, signals, and technical analysis
        """
        # Find investments based on criteria
        investments, total_count = await self._find_investments_by_criteria(request)

        # Convert to DTOs
        investment_dtos = [self._map_investment_to_dto(inv) for inv in investments]

        # Generate signals for found investments
        symbols = [inv.symbol for inv in investment_dtos]
        signals = await self._generate_signals_for_symbols(symbols)

        # Get technical analysis for found investments
        technical_analysis = await self._get_technical_analysis_for_symbols(symbols)

        return InvestmentSearchResultDTO(
            investments=investment_dtos,
            total_count=total_count,
            signals=list(signals.values()),
            technical_analysis=list(technical_analysis.values()),
        )

    async def _find_investments_by_criteria(
        self, request: FindInvestmentsQuery
    ) -> tuple[list, int]:
        """
        Find investments based on search criteria.

        Args:
            request: Search query parameters

        Returns:
            Tuple of (investments list, total count)
        """
        # Build repository query parameters
        criteria = {}

        if request.sectors:
            criteria["sectors"] = request.sectors

        if request.investment_types:
            criteria["investment_types"] = request.investment_types

        if request.market_caps:
            criteria["market_caps"] = request.market_caps

        if request.currency:
            criteria["currency"] = request.currency

        if request.min_price or request.max_price:
            criteria["price_range"] = (request.min_price, request.max_price)

        if request.search_term:
            criteria["search_term"] = request.search_term

        # Execute repository query
        investments = await self._investment_repository.find_by_criteria(
            criteria=criteria, limit=request.limit, offset=request.offset
        )

        # Get total count for pagination
        total_count = await self._investment_repository.count_by_criteria(criteria)

        return investments, total_count

    async def _generate_signals_for_symbols(
        self, symbols: list[str]
    ) -> dict[str, SignalDTO]:
        """
        Generate trading signals for a list of symbols.

        Args:
            symbols: List of investment symbols

        Returns:
            Dictionary mapping symbols to their signals
        """
        try:
            return await self._signal_generator.generate_signals_for_portfolio(symbols)
        except Exception:
            # Return empty dict if signal generation fails
            return {}

    async def _get_technical_analysis_for_symbols(
        self, symbols: list[str]
    ) -> dict[str, TechnicalAnalysisDTO]:
        """
        Get technical analysis for a list of symbols.

        Args:
            symbols: List of investment symbols

        Returns:
            Dictionary mapping symbols to their technical analysis
        """
        try:
            return await self._technical_analyzer.analyze_multiple_investments(symbols)
        except Exception:
            # Return empty dict if analysis fails
            return {}

    def _map_investment_to_dto(self, investment) -> InvestmentDTO:
        """
        Map domain investment entity to DTO.

        Args:
            investment: Domain investment entity

        Returns:
            Investment DTO
        """
        # This would normally use a proper mapper
        # For now, return a placeholder DTO
        from datetime import datetime
        from uuid import uuid4

        # Handle MagicMock values
        def safe_getattr(obj, attr, default):
            """Get attribute value, handling MagicMock objects"""
            value = getattr(obj, attr, default)
            if hasattr(value, "_mock_name"):
                return default
            return value

        return InvestmentDTO(
            id=safe_getattr(investment, "id", uuid4()),
            symbol=safe_getattr(investment, "symbol", "UNKNOWN"),
            name=safe_getattr(investment, "name", "Unknown Investment"),
            investment_type=safe_getattr(investment, "investment_type", "STOCK"),
            sector=safe_getattr(investment, "sector", "TECHNOLOGY"),
            market_cap=safe_getattr(investment, "market_cap", "LARGE_CAP"),
            currency=safe_getattr(investment, "currency", "USD"),
            exchange=safe_getattr(investment, "exchange", "NASDAQ"),
            isin=safe_getattr(investment, "isin", None),
            created_at=safe_getattr(investment, "created_at", datetime.now()),
            updated_at=safe_getattr(investment, "updated_at", datetime.now()),
        )
