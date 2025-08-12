"""
Integration Tests for CQRS Handlers
===================================

Tests for command and query handlers to ensure proper
CQRS implementation and handler coordination.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.application.commands import (
    AddInvestmentToPortfolioCommand,
    CreateInvestmentCommand,
    CreatePortfolioCommand,
)
from src.application.handlers.command_handlers import (
    AddInvestmentToPortfolioCommandHandler,
    CreateInvestmentCommandHandler,
    CreatePortfolioCommandHandler,
)
from src.application.handlers.query_handlers import (
    FindInvestmentsQueryHandler,
    GetInvestmentByIdQueryHandler,
    GetPortfolioByIdQueryHandler,
)
from src.application.queries import (
    FindInvestmentsQuery,
    GetInvestmentByIdQuery,
    GetPortfolioByIdQuery,
)


class TestCommandHandlers:
    """Test suite for command handlers"""

    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories for handlers"""
        investment_repo = AsyncMock()
        portfolio_repo = AsyncMock()
        user_repo = AsyncMock()
        unit_of_work = AsyncMock()

        return {
            "investment_repo": investment_repo,
            "portfolio_repo": portfolio_repo,
            "user_repo": user_repo,
            "unit_of_work": unit_of_work,
        }

    @pytest.mark.asyncio
    async def test_create_investment_command_handler(self, mock_repositories):
        """Test create investment command handler"""
        # Arrange
        handler = CreateInvestmentCommandHandler(
            investment_repository=mock_repositories["investment_repo"],
            unit_of_work=mock_repositories["unit_of_work"],
        )

        command = CreateInvestmentCommand(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type="STOCK",
            sector="TECHNOLOGY",
            market_cap="LARGE_CAP",
            currency="USD",
            exchange="NASDAQ",
            isin="US0378331005",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result is not None
        mock_repositories["investment_repo"].save.assert_called_once()
        mock_repositories["unit_of_work"].commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_portfolio_command_handler(self, mock_repositories):
        """Test create portfolio command handler"""
        # Arrange
        user_id = uuid4()
        mock_repositories["user_repo"].find_by_id.return_value = MagicMock(id=user_id)

        handler = CreatePortfolioCommandHandler(
            portfolio_repository=mock_repositories["portfolio_repo"],
            user_repository=mock_repositories["user_repo"],
            unit_of_work=mock_repositories["unit_of_work"],
        )

        command = CreatePortfolioCommand(
            user_id=user_id,
            name="My Portfolio",
            description="Test portfolio",
            initial_cash_amount=10000.0,
            currency="USD",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result is not None
        mock_repositories["user_repo"].find_by_id.assert_called_once_with(user_id)
        mock_repositories["portfolio_repo"].save.assert_called_once()
        mock_repositories["unit_of_work"].commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_portfolio_user_not_found(self, mock_repositories):
        """Test create portfolio with non-existent user"""
        # Arrange
        user_id = uuid4()
        mock_repositories["user_repo"].find_by_id.return_value = None

        handler = CreatePortfolioCommandHandler(
            portfolio_repository=mock_repositories["portfolio_repo"],
            user_repository=mock_repositories["user_repo"],
            unit_of_work=mock_repositories["unit_of_work"],
        )

        command = CreatePortfolioCommand(user_id=user_id, name="My Portfolio")

        # Act & Assert
        with pytest.raises(ValueError, match=f"User {user_id} not found"):
            await handler.handle(command)

    @pytest.mark.asyncio
    async def test_add_investment_to_portfolio_handler(self, mock_repositories):
        """Test add investment to portfolio command handler"""
        # Arrange
        portfolio_id = uuid4()
        investment_id = uuid4()

        # Mock portfolio with sufficient cash
        mock_portfolio = MagicMock()
        mock_portfolio.cash_balance = MagicMock()
        mock_portfolio.cash_balance.amount = 10000.0
        mock_portfolio.add_investment = MagicMock()

        mock_investment = MagicMock()

        mock_repositories["portfolio_repo"].find_by_id.return_value = mock_portfolio
        mock_repositories["investment_repo"].find_by_id.return_value = mock_investment

        handler = AddInvestmentToPortfolioCommandHandler(
            portfolio_repository=mock_repositories["portfolio_repo"],
            investment_repository=mock_repositories["investment_repo"],
            unit_of_work=mock_repositories["unit_of_work"],
        )

        command = AddInvestmentToPortfolioCommand(
            portfolio_id=portfolio_id,
            investment_id=investment_id,
            quantity=10,
            purchase_price=150.0,
            currency="USD",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result is True
        mock_portfolio.add_investment.assert_called_once()
        mock_repositories["portfolio_repo"].save.assert_called_once()
        mock_repositories["unit_of_work"].commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_investment_insufficient_cash(self, mock_repositories):
        """Test add investment with insufficient cash"""
        # Arrange
        portfolio_id = uuid4()
        investment_id = uuid4()

        # Mock portfolio with insufficient cash
        mock_portfolio = MagicMock()
        mock_portfolio.cash_balance = MagicMock()
        mock_portfolio.cash_balance.amount = 100.0  # Insufficient for 10 * 150.0

        mock_investment = MagicMock()

        mock_repositories["portfolio_repo"].find_by_id.return_value = mock_portfolio
        mock_repositories["investment_repo"].find_by_id.return_value = mock_investment

        handler = AddInvestmentToPortfolioCommandHandler(
            portfolio_repository=mock_repositories["portfolio_repo"],
            investment_repository=mock_repositories["investment_repo"],
            unit_of_work=mock_repositories["unit_of_work"],
        )

        command = AddInvestmentToPortfolioCommand(
            portfolio_id=portfolio_id,
            investment_id=investment_id,
            quantity=10,
            purchase_price=150.0,
            currency="USD",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Insufficient cash balance"):
            await handler.handle(command)


class TestQueryHandlers:
    """Test suite for query handlers"""

    @pytest.fixture
    def mock_use_cases(self):
        """Mock use cases for query handlers"""
        find_investments_use_case = AsyncMock()
        analyze_portfolio_use_case = AsyncMock()

        return {
            "find_investments": find_investments_use_case,
            "analyze_portfolio": analyze_portfolio_use_case,
        }

    @pytest.fixture
    def mock_repositories(self):
        """Mock repositories for query handlers"""
        investment_repo = AsyncMock()
        portfolio_repo = AsyncMock()

        return {"investment_repo": investment_repo, "portfolio_repo": portfolio_repo}

    @pytest.mark.asyncio
    async def test_find_investments_query_handler(self, mock_use_cases):
        """Test find investments query handler"""
        # Arrange
        mock_result = MagicMock()
        mock_use_cases["find_investments"].execute.return_value = mock_result

        handler = FindInvestmentsQueryHandler(
            find_investments_use_case=mock_use_cases["find_investments"]
        )

        query = FindInvestmentsQuery(sectors=["TECHNOLOGY"], limit=20)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result == mock_result
        mock_use_cases["find_investments"].execute.assert_called_once_with(query)

    @pytest.mark.asyncio
    async def test_get_investment_by_id_handler(self, mock_repositories):
        """Test get investment by ID query handler"""
        # Arrange
        investment_id = uuid4()
        mock_investment = MagicMock()
        mock_repositories["investment_repo"].find_by_id.return_value = mock_investment

        handler = GetInvestmentByIdQueryHandler(
            investment_repository=mock_repositories["investment_repo"]
        )

        query = GetInvestmentByIdQuery(investment_id=investment_id)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        mock_repositories["investment_repo"].find_by_id.assert_called_once_with(
            investment_id
        )

    @pytest.mark.asyncio
    async def test_get_investment_by_id_not_found(self, mock_repositories):
        """Test get investment by ID when investment not found"""
        # Arrange
        investment_id = uuid4()
        mock_repositories["investment_repo"].find_by_id.return_value = None

        handler = GetInvestmentByIdQueryHandler(
            investment_repository=mock_repositories["investment_repo"]
        )

        query = GetInvestmentByIdQuery(investment_id=investment_id)

        # Act & Assert
        with pytest.raises(ValueError, match=f"Investment {investment_id} not found"):
            await handler.handle(query)

    @pytest.mark.asyncio
    async def test_get_portfolio_by_id_handler(self, mock_repositories):
        """Test get portfolio by ID query handler"""
        # Arrange
        portfolio_id = uuid4()
        mock_portfolio = MagicMock()
        mock_repositories["portfolio_repo"].find_by_id.return_value = mock_portfolio

        handler = GetPortfolioByIdQueryHandler(
            portfolio_repository=mock_repositories["portfolio_repo"]
        )

        query = GetPortfolioByIdQuery(portfolio_id=portfolio_id, include_positions=True)

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None
        mock_repositories["portfolio_repo"].find_by_id.assert_called_once_with(
            portfolio_id
        )

    @pytest.mark.asyncio
    async def test_get_portfolio_by_id_not_found(self, mock_repositories):
        """Test get portfolio by ID when portfolio not found"""
        # Arrange
        portfolio_id = uuid4()
        mock_repositories["portfolio_repo"].find_by_id.return_value = None

        handler = GetPortfolioByIdQueryHandler(
            portfolio_repository=mock_repositories["portfolio_repo"]
        )

        query = GetPortfolioByIdQuery(portfolio_id=portfolio_id)

        # Act & Assert
        with pytest.raises(ValueError, match=f"Portfolio {portfolio_id} not found"):
            await handler.handle(query)
