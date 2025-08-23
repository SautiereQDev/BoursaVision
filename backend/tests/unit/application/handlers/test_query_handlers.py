"""
Tests for Query Handlers
========================

Tests complets pour les gestionnaires de requêtes CQRS.
Test des opérations de lecture, transformation et gestion d'erreurs.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from boursa_vision.application.handlers.query_handlers import (
    AnalyzePortfolioQueryHandler,
    FindInvestmentsQueryHandler,
    GetInvestmentByIdQueryHandler,
    GetPortfolioByIdQueryHandler,
    GetUserPortfoliosQueryHandler,
)
from boursa_vision.application.queries.investment.find_investments_query import (
    FindInvestmentsQuery,
)
from boursa_vision.application.queries.investment.get_investment_by_id_query import (
    GetInvestmentByIdQuery,
)
from boursa_vision.application.queries.portfolio.analyze_portfolio_query import (
    AnalyzePortfolioQuery,
)
from boursa_vision.application.queries.portfolio.get_portfolio_by_id_query import (
    GetPortfolioByIdQuery,
)


class TestFindInvestmentsQueryHandler:
    """Tests pour FindInvestmentsQueryHandler"""

    @pytest.fixture
    def mock_find_investments_use_case(self):
        """Mock use case pour la recherche d'investissements"""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_find_investments_use_case):
        """Handler avec dépendances mockées"""
        return FindInvestmentsQueryHandler(
            find_investments_use_case=mock_find_investments_use_case
        )

    @pytest.fixture
    def find_investments_query(self):
        """Query de recherche d'investissements"""
        return FindInvestmentsQuery(
            sectors=["Technology"],
            search_term="Apple",
            limit=10,
        )

    @pytest.fixture
    def mock_search_result(self):
        """Mock résultat de recherche"""
        result = MagicMock()
        result.investments = []
        result.total_count = 0
        result.page = 1
        result.page_size = 10
        return result

    def test_handler_initialization(self, mock_find_investments_use_case):
        """Test l'initialisation du handler"""
        handler = FindInvestmentsQueryHandler(
            find_investments_use_case=mock_find_investments_use_case
        )

        assert handler._find_investments_use_case == mock_find_investments_use_case

    async def test_handle_find_investments_success(
        self,
        handler,
        find_investments_query,
        mock_search_result,
        mock_find_investments_use_case,
    ):
        """Test recherche d'investissements réussie"""
        # Arrange
        mock_find_investments_use_case.execute.return_value = mock_search_result

        # Act
        result = await handler.handle(find_investments_query)

        # Assert
        assert result == mock_search_result
        mock_find_investments_use_case.execute.assert_called_once_with(
            find_investments_query
        )

    async def test_handle_use_case_error(
        self, handler, find_investments_query, mock_find_investments_use_case
    ):
        """Test gestion d'erreur du use case"""
        # Arrange
        mock_find_investments_use_case.execute.side_effect = Exception("Use case error")

        # Act & Assert
        with pytest.raises(Exception, match="Use case error"):
            await handler.handle(find_investments_query)

    async def test_handle_empty_query(
        self, handler, mock_find_investments_use_case, mock_search_result
    ):
        """Test avec query vide"""
        query = FindInvestmentsQuery()
        mock_find_investments_use_case.execute.return_value = mock_search_result

        # Act
        result = await handler.handle(query)

        # Assert
        assert result == mock_search_result
        mock_find_investments_use_case.execute.assert_called_once_with(query)


class TestGetInvestmentByIdQueryHandler:
    """Tests pour GetInvestmentByIdQueryHandler"""

    @pytest.fixture
    def mock_investment_repository(self):
        """Mock repository pour les investissements"""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_investment_repository):
        """Handler avec dépendances mockées"""
        return GetInvestmentByIdQueryHandler(
            investment_repository=mock_investment_repository
        )

    @pytest.fixture
    def get_investment_query(self):
        """Query pour récupérer un investissement"""
        return GetInvestmentByIdQuery(investment_id=uuid4())

    @pytest.fixture
    def mock_investment(self):
        """Mock investissement"""
        investment = MagicMock()
        investment.id = uuid4()
        investment.symbol = "AAPL"
        investment.name = "Apple Inc."
        investment.investment_type = "STOCK"
        investment.sector = "Technology"
        investment.market_cap = "Large Cap"
        investment.currency = "USD"
        investment.exchange = "NASDAQ"
        investment.isin = "US0378331005"
        investment.created_at = datetime.now()
        return investment

    def test_handler_initialization(self, mock_investment_repository):
        """Test l'initialisation du handler"""
        handler = GetInvestmentByIdQueryHandler(
            investment_repository=mock_investment_repository
        )

        assert handler._investment_repository == mock_investment_repository

    async def test_handle_get_investment_success(
        self, handler, get_investment_query, mock_investment, mock_investment_repository
    ):
        """Test récupération d'investissement réussie"""
        # Arrange
        mock_investment_repository.find_by_id.return_value = mock_investment

        # Act
        result = await handler.handle(get_investment_query)

        # Assert
        assert hasattr(result, "symbol") or isinstance(result, dict)
        mock_investment_repository.find_by_id.assert_called_once_with(
            get_investment_query.investment_id
        )

    async def test_handle_investment_not_found(
        self, handler, get_investment_query, mock_investment_repository
    ):
        """Test erreur investissement non trouvé"""
        # Arrange
        mock_investment_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Investment .+ not found"):
            await handler.handle(get_investment_query)

        mock_investment_repository.find_by_id.assert_called_once_with(
            get_investment_query.investment_id
        )

    async def test_handle_repository_error(
        self, handler, get_investment_query, mock_investment_repository
    ):
        """Test gestion d'erreur du repository"""
        # Arrange
        mock_investment_repository.find_by_id.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await handler.handle(get_investment_query)

    def test_map_investment_to_dto_method(self, handler, mock_investment):
        """Test méthode de mapping vers DTO"""
        # Act
        result = handler._map_investment_to_dto(mock_investment)

        # Assert
        assert result is not None
        # Le mapping est délégué au mapper, donc on vérifie juste qu'il est appelé


class TestGetPortfolioByIdQueryHandler:
    """Tests pour GetPortfolioByIdQueryHandler"""

    @pytest.fixture
    def mock_portfolio_repository(self):
        """Mock repository pour les portfolios"""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_portfolio_repository):
        """Handler avec dépendances mockées"""
        return GetPortfolioByIdQueryHandler(
            portfolio_repository=mock_portfolio_repository
        )

    @pytest.fixture
    def get_portfolio_query(self):
        """Query pour récupérer un portfolio"""
        return GetPortfolioByIdQuery(portfolio_id=uuid4(), include_positions=True)

    @pytest.fixture
    def mock_portfolio(self):
        """Mock portfolio"""
        portfolio = MagicMock()
        portfolio.id = uuid4()
        portfolio.user_id = uuid4()
        portfolio.name = "Test Portfolio"
        portfolio.description = "Test description"
        portfolio.currency = "USD"
        portfolio.cash_balance = MagicMock()
        portfolio.cash_balance.amount = 1000.0
        portfolio.cash_balance.currency = "USD"
        portfolio.created_at = datetime.now()
        portfolio.updated_at = datetime.now()
        return portfolio

    def test_handler_initialization(self, mock_portfolio_repository):
        """Test l'initialisation du handler"""
        handler = GetPortfolioByIdQueryHandler(
            portfolio_repository=mock_portfolio_repository
        )

        assert handler._portfolio_repository == mock_portfolio_repository

    async def test_handle_get_portfolio_success(
        self, handler, get_portfolio_query, mock_portfolio, mock_portfolio_repository
    ):
        """Test récupération de portfolio réussie"""
        # Arrange
        mock_portfolio_repository.find_by_id.return_value = mock_portfolio

        # Act
        result = await handler.handle(get_portfolio_query)

        # Assert
        assert result is not None
        mock_portfolio_repository.find_by_id.assert_called_once_with(
            get_portfolio_query.portfolio_id
        )

    async def test_handle_portfolio_not_found(
        self, handler, get_portfolio_query, mock_portfolio_repository
    ):
        """Test erreur portfolio non trouvé"""
        # Arrange
        mock_portfolio_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Portfolio .+ not found"):
            await handler.handle(get_portfolio_query)

    async def test_handle_portfolio_without_positions(
        self, mock_portfolio_repository, mock_portfolio
    ):
        """Test récupération de portfolio sans positions"""
        handler = GetPortfolioByIdQueryHandler(
            portfolio_repository=mock_portfolio_repository
        )

        query = GetPortfolioByIdQuery(portfolio_id=uuid4(), include_positions=False)

        mock_portfolio_repository.find_by_id.return_value = mock_portfolio

        # Act
        result = await handler.handle(query)

        # Assert
        assert result is not None

    def test_map_portfolio_to_dto_method(self, handler, mock_portfolio):
        """Test méthode de mapping vers DTO"""
        # Act
        result = handler._map_portfolio_to_dto(mock_portfolio, include_positions=True)

        # Assert
        assert result is not None


class TestAnalyzePortfolioQueryHandler:
    """Tests pour AnalyzePortfolioQueryHandler"""

    @pytest.fixture
    def mock_analyze_portfolio_use_case(self):
        """Mock use case pour l'analyse de portfolio"""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_analyze_portfolio_use_case):
        """Handler avec dépendances mockées"""
        return AnalyzePortfolioQueryHandler(
            analyze_portfolio_use_case=mock_analyze_portfolio_use_case
        )

    @pytest.fixture
    def analyze_portfolio_query(self):
        """Query d'analyse de portfolio"""
        return AnalyzePortfolioQuery(
            portfolio_id=uuid4(),
            benchmark_symbol="SPY",
            include_technical_analysis=True,
        )

    @pytest.fixture
    def mock_analysis_result(self):
        """Mock résultat d'analyse"""
        result = MagicMock()
        result.portfolio_id = uuid4()
        result.total_value = 15000.0
        result.total_return = 0.15
        result.risk_score = 0.6
        result.recommendations = []
        return result

    def test_handler_initialization(self, mock_analyze_portfolio_use_case):
        """Test l'initialisation du handler"""
        handler = AnalyzePortfolioQueryHandler(
            analyze_portfolio_use_case=mock_analyze_portfolio_use_case
        )

        assert handler._analyze_portfolio_use_case == mock_analyze_portfolio_use_case

    async def test_handle_analyze_portfolio_success(
        self,
        handler,
        analyze_portfolio_query,
        mock_analysis_result,
        mock_analyze_portfolio_use_case,
    ):
        """Test analyse de portfolio réussie"""
        # Arrange
        mock_analyze_portfolio_use_case.execute.return_value = mock_analysis_result

        # Act
        result = await handler.handle(analyze_portfolio_query)

        # Assert
        assert result == mock_analysis_result
        mock_analyze_portfolio_use_case.execute.assert_called_once_with(
            analyze_portfolio_query
        )

    async def test_handle_use_case_error(
        self, handler, analyze_portfolio_query, mock_analyze_portfolio_use_case
    ):
        """Test gestion d'erreur du use case"""
        # Arrange
        mock_analyze_portfolio_use_case.execute.side_effect = Exception(
            "Analysis error"
        )

        # Act & Assert
        with pytest.raises(Exception, match="Analysis error"):
            await handler.handle(analyze_portfolio_query)

    async def test_handle_analyze_without_benchmark(
        self, mock_analyze_portfolio_use_case, mock_analysis_result
    ):
        """Test analyse sans benchmark"""
        handler = AnalyzePortfolioQueryHandler(
            analyze_portfolio_use_case=mock_analyze_portfolio_use_case
        )

        query = AnalyzePortfolioQuery(
            portfolio_id=uuid4(), include_technical_analysis=False
        )

        mock_analyze_portfolio_use_case.execute.return_value = mock_analysis_result

        # Act
        result = await handler.handle(query)

        # Assert
        assert result == mock_analysis_result


class TestGetUserPortfoliosQueryHandler:
    """Tests pour GetUserPortfoliosQueryHandler"""

    @pytest.fixture
    def mock_portfolio_repository(self):
        """Mock repository pour les portfolios"""
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_portfolio_repository):
        """Handler avec dépendances mockées"""
        return GetUserPortfoliosQueryHandler(
            portfolio_repository=mock_portfolio_repository
        )

    @pytest.fixture
    def user_portfolios_query(self):
        """Query pour les portfolios d'un utilisateur"""
        return {"user_id": uuid4(), "include_positions": True}

    @pytest.fixture
    def mock_portfolios(self):
        """Mock liste de portfolios"""
        portfolio1 = MagicMock()
        portfolio1.id = uuid4()
        portfolio1.user_id = uuid4()
        portfolio1.name = "Portfolio 1"
        portfolio1.description = "Description 1"
        portfolio1.currency = "USD"
        portfolio1.cash_balance = 1000.0
        portfolio1.created_at = datetime.now()
        portfolio1.updated_at = datetime.now()

        portfolio2 = MagicMock()
        portfolio2.id = uuid4()
        portfolio2.user_id = uuid4()
        portfolio2.name = "Portfolio 2"
        portfolio2.description = "Description 2"
        portfolio2.currency = "EUR"
        portfolio2.cash_balance = 2000.0
        portfolio2.created_at = datetime.now()
        portfolio2.updated_at = datetime.now()

        return [portfolio1, portfolio2]

    def test_handler_initialization(self, mock_portfolio_repository):
        """Test l'initialisation du handler"""
        handler = GetUserPortfoliosQueryHandler(
            portfolio_repository=mock_portfolio_repository
        )

        assert handler._portfolio_repository == mock_portfolio_repository

    async def test_handle_get_user_portfolios_success(
        self, handler, user_portfolios_query, mock_portfolios, mock_portfolio_repository
    ):
        """Test récupération des portfolios utilisateur réussie"""
        # Arrange
        mock_portfolio_repository.find_by_user_id.return_value = mock_portfolios

        # Act
        result = await handler.handle(user_portfolios_query)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        mock_portfolio_repository.find_by_user_id.assert_called_once_with(
            user_portfolios_query["user_id"]
        )

    async def test_handle_no_portfolios_found(
        self, handler, user_portfolios_query, mock_portfolio_repository
    ):
        """Test aucun portfolio trouvé"""
        # Arrange
        mock_portfolio_repository.find_by_user_id.return_value = []

        # Act
        result = await handler.handle(user_portfolios_query)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 0

    async def test_handle_query_without_positions(
        self, handler, mock_portfolios, mock_portfolio_repository
    ):
        """Test query sans inclure les positions"""
        query = {"user_id": uuid4(), "include_positions": False}

        mock_portfolio_repository.find_by_user_id.return_value = mock_portfolios

        # Act
        result = await handler.handle(query)

        # Assert
        assert isinstance(result, list)
        assert len(result) == 2

    async def test_handle_repository_error(
        self, handler, user_portfolios_query, mock_portfolio_repository
    ):
        """Test gestion d'erreur du repository"""
        # Arrange
        mock_portfolio_repository.find_by_user_id.side_effect = Exception(
            "Database error"
        )

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await handler.handle(user_portfolios_query)

    def test_map_portfolio_to_dto_method(self, handler):
        """Test méthode de mapping vers DTO"""
        # Mock portfolio minimal avec tous les champs requis
        portfolio = MagicMock()
        portfolio.id = uuid4()
        portfolio.user_id = uuid4()
        portfolio.name = "Test Portfolio"
        portfolio.description = "Test description"
        portfolio.cash_balance = 1500.0
        portfolio.created_at = datetime.now()
        portfolio.updated_at = datetime.now()

        # Act
        result = handler._map_portfolio_to_dto(portfolio, include_positions=True)

        # Assert
        assert hasattr(result, "id") or "id" in result
        assert hasattr(result, "name") or "name" in result


class TestQueryHandlersIntegration:
    """Tests d'intégration entre les query handlers"""

    def test_all_handlers_implement_required_interface(self):
        """Test que tous les handlers implémentent l'interface requise"""
        handlers = [
            FindInvestmentsQueryHandler,
            GetInvestmentByIdQueryHandler,
            GetPortfolioByIdQueryHandler,
            AnalyzePortfolioQueryHandler,
            GetUserPortfoliosQueryHandler,
        ]

        for handler_class in handlers:
            assert hasattr(handler_class, "handle"), (
                f"{handler_class.__name__} must have handle method"
            )

    def test_handlers_dependency_injection(self):
        """Test l'injection de dépendances dans tous les handlers"""
        # Test avec mocks
        mock_repo = AsyncMock()
        mock_use_case = AsyncMock()

        # Création de tous les handlers
        find_investments_handler = FindInvestmentsQueryHandler(mock_use_case)
        get_investment_handler = GetInvestmentByIdQueryHandler(mock_repo)
        get_portfolio_handler = GetPortfolioByIdQueryHandler(mock_repo)
        analyze_portfolio_handler = AnalyzePortfolioQueryHandler(mock_use_case)
        get_user_portfolios_handler = GetUserPortfoliosQueryHandler(mock_repo)

        # Vérification de l'injection
        assert find_investments_handler._find_investments_use_case is mock_use_case
        assert get_investment_handler._investment_repository is mock_repo
        assert get_portfolio_handler._portfolio_repository is mock_repo
        assert analyze_portfolio_handler._analyze_portfolio_use_case is mock_use_case
        assert get_user_portfolios_handler._portfolio_repository is mock_repo

    def test_query_handlers_async_compatibility(self):
        """Test que tous les handlers sont compatibles async"""
        import inspect

        handlers = [
            FindInvestmentsQueryHandler,
            GetInvestmentByIdQueryHandler,
            GetPortfolioByIdQueryHandler,
            AnalyzePortfolioQueryHandler,
            GetUserPortfoliosQueryHandler,
        ]

        for handler_class in handlers:
            handle_method = handler_class.handle
            assert inspect.iscoroutinefunction(handle_method), (
                f"{handler_class.__name__}.handle must be async"
            )

    def test_handlers_error_propagation(self):
        """Test que les handlers propagent correctement les erreurs"""
        # Ce test vérifie que les handlers ne masquent pas les erreurs inattendues
        mock_repo = AsyncMock()
        mock_repo.find_by_id.side_effect = RuntimeError("Critical error")

        handler = GetInvestmentByIdQueryHandler(mock_repo)
        query = GetInvestmentByIdQuery(investment_id=uuid4())

        # Test async context
        async def test_error_propagation():
            with pytest.raises(RuntimeError, match="Critical error"):
                await handler.handle(query)

        # Run the test
        import asyncio

        asyncio.run(test_error_propagation())
