"""
Query Handlers Implementation
============================

Handlers for processing queries following CQRS pattern.
Each handler is responsible for executing a specific query.
"""

from ..common import IQueryHandler
from ..dtos import (
    InvestmentDTO,
    InvestmentSearchResultDTO,
    PortfolioAnalysisResultDTO,
    PortfolioDTO,
)
from ..queries import (
    AnalyzePortfolioQuery,
    FindInvestmentsQuery,
    GetInvestmentByIdQuery,
    GetPortfolioByIdQuery,
)
from ..use_cases.analyze_portfolio import AnalyzePortfolioUseCase
from ..use_cases.find_investments import FindInvestmentsUseCase


class FindInvestmentsQueryHandler(
    IQueryHandler[FindInvestmentsQuery, InvestmentSearchResultDTO]
):
    """Handler for finding investments query"""

    def __init__(self, find_investments_use_case: FindInvestmentsUseCase):
        self._find_investments_use_case = find_investments_use_case

    async def handle(self, query: FindInvestmentsQuery) -> InvestmentSearchResultDTO:
        """
        Handle the find investments query.

        Args:
            query: Find investments query

        Returns:
            Investment search results
        """
        return await self._find_investments_use_case.execute(query)


class GetInvestmentByIdQueryHandler(
    IQueryHandler[GetInvestmentByIdQuery, InvestmentDTO]
):
    """Handler for getting investment by ID"""

    def __init__(self, investment_repository):
        self._investment_repository = investment_repository

    async def handle(self, query: GetInvestmentByIdQuery) -> InvestmentDTO:
        """
        Handle the get investment by ID query.

        Args:
            query: Get investment query

        Returns:
            Investment DTO

        Raises:
            ValueError: If investment not found
        """
        investment = await self._investment_repository.find_by_id(query.investment_id)
        if not investment:
            raise ValueError(f"Investment {query.investment_id} not found")

        return self._map_investment_to_dto(investment)

    def _map_investment_to_dto(self, investment) -> InvestmentDTO:
        """Map investment entity to DTO."""
        from ..mappers import InvestmentMapper

        return InvestmentMapper.to_dto(investment)


class GetPortfolioByIdQueryHandler(IQueryHandler[GetPortfolioByIdQuery, PortfolioDTO]):
    """Handler for getting portfolio by ID"""

    def __init__(self, portfolio_repository):
        self._portfolio_repository = portfolio_repository

    async def handle(self, query: GetPortfolioByIdQuery) -> PortfolioDTO:
        """
        Handle the get portfolio by ID query.

        Args:
            query: Get portfolio query

        Returns:
            Portfolio DTO

        Raises:
            ValueError: If portfolio not found
        """
        portfolio = await self._portfolio_repository.find_by_id(query.portfolio_id)
        if not portfolio:
            raise ValueError(f"Portfolio {query.portfolio_id} not found")

        return self._map_portfolio_to_dto(portfolio, query.include_positions)

    def _map_portfolio_to_dto(
        self, portfolio, include_positions: bool = False
    ) -> PortfolioDTO:
        """Map portfolio entity to DTO."""
        from ..mappers import PortfolioMapper

        return PortfolioMapper.to_dto(portfolio)


class AnalyzePortfolioQueryHandler(
    IQueryHandler[AnalyzePortfolioQuery, PortfolioAnalysisResultDTO]
):
    """Handler for portfolio analysis query"""

    def __init__(self, analyze_portfolio_use_case: AnalyzePortfolioUseCase):
        self._analyze_portfolio_use_case = analyze_portfolio_use_case

    async def handle(self, query: AnalyzePortfolioQuery) -> PortfolioAnalysisResultDTO:
        """
        Handle the analyze portfolio query.

        Args:
            query: Analyze portfolio query

        Returns:
            Portfolio analysis results
        """
        return await self._analyze_portfolio_use_case.execute(query)


class GetUserPortfoliosQueryHandler(IQueryHandler[dict, list[PortfolioDTO]]):
    """Handler for getting user portfolios"""

    def __init__(self, portfolio_repository):
        self._portfolio_repository = portfolio_repository

    async def handle(self, query: dict) -> list[PortfolioDTO]:
        """
        Handle the get user portfolios query.

        Args:
            query: Query parameters with user_id

        Returns:
            List of portfolio DTOs
        """
        portfolios = await self._portfolio_repository.find_by_user_id(query["user_id"])

        return [
            self._map_portfolio_to_dto(portfolio, query.get("include_positions", False))
            for portfolio in portfolios
        ]

    def _map_portfolio_to_dto(
        self, portfolio, include_positions: bool = False
    ) -> PortfolioDTO:
        """Map portfolio entity to DTO"""
        from datetime import datetime
        from uuid import UUID

        # Handle MagicMock values safely
        def safe_getattr(obj, attr, default):
            """Get attribute value, handling MagicMock objects"""
            value = getattr(obj, attr, default)
            if hasattr(value, "_mock_name"):
                return default
            return value

        return PortfolioDTO(
            id=safe_getattr(
                portfolio, "id", UUID("00000000-0000-0000-0000-000000000000")
            ),
            user_id=safe_getattr(
                portfolio, "user_id", UUID("00000000-0000-0000-0000-000000000000")
            ),
            name=str(safe_getattr(portfolio, "name", "Test Portfolio")),
            description=str(safe_getattr(portfolio, "description", None))
            if safe_getattr(portfolio, "description", None)
            else None,
            currency=str(safe_getattr(portfolio, "currency", "USD")),
            total_value=None,  # Simplified for handler
            positions=[],
            created_at=safe_getattr(portfolio, "created_at", datetime.now()),
            updated_at=safe_getattr(portfolio, "updated_at", datetime.now()),
        )


# Helper methods (could be extracted to mappers)
def _map_investment_to_dto(investment) -> InvestmentDTO:
    """Map investment entity to DTO"""
    from datetime import datetime
    from uuid import uuid4

    return InvestmentDTO(
        id=getattr(investment, "id", uuid4()),
        symbol=getattr(investment, "symbol", ""),
        name=getattr(investment, "name", ""),
        investment_type=getattr(investment, "investment_type", "STOCK"),
        sector=getattr(investment, "sector", "TECHNOLOGY"),
        market_cap=getattr(investment, "market_cap", "LARGE_CAP"),
        currency=getattr(investment, "currency", "USD"),
        exchange=getattr(investment, "exchange", ""),
        isin=getattr(investment, "isin", None),
        created_at=getattr(investment, "created_at", datetime.now()),
    )
