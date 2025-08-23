"""
Tests for Command Handlers
==========================

Tests complets pour les gestionnaires de commandes CQRS.
Test des opérations d'écriture, validation et gestion d'erreurs.
"""

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from boursa_vision.application.commands.investment.create_investment_command import (
    CreateInvestmentCommand,
)
from boursa_vision.application.commands.portfolio.add_investment_to_portfolio_command import (
    AddInvestmentToPortfolioCommand,
)
from boursa_vision.application.commands.portfolio.create_portfolio_command import (
    CreatePortfolioCommand,
)
from boursa_vision.application.commands.signal.generate_signal_command import (
    GenerateSignalCommand,
)
from boursa_vision.application.handlers.command_handlers import (
    AddInvestmentToPortfolioCommandHandler,
    CreateInvestmentCommandHandler,
    CreatePortfolioCommandHandler,
    GenerateSignalCommandHandler,
)


class TestCreateInvestmentCommandHandler:
    """Tests pour CreateInvestmentCommandHandler"""

    @pytest.fixture
    def mock_investment_repository(self):
        """Mock repository pour les investissements"""
        return AsyncMock()

    @pytest.fixture
    def mock_unit_of_work(self):
        """Mock unit of work"""
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        return mock_uow

    @pytest.fixture
    def handler(self, mock_investment_repository, mock_unit_of_work):
        """Handler avec dépendances mockées"""
        return CreateInvestmentCommandHandler(
            investment_repository=mock_investment_repository,
            unit_of_work=mock_unit_of_work,
        )

    @pytest.fixture
    def create_investment_command(self):
        """Command de création d'investissement"""
        return CreateInvestmentCommand(
            symbol="AAPL",
            name="Apple Inc.",
            investment_type="Stock",
            sector="Technology",
            market_cap="Large Cap",
            currency="USD",
            exchange="NASDAQ",
            isin="US0378331005",
        )

    def test_handler_initialization(
        self, mock_investment_repository, mock_unit_of_work
    ):
        """Test l'initialisation du handler"""
        handler = CreateInvestmentCommandHandler(
            investment_repository=mock_investment_repository,
            unit_of_work=mock_unit_of_work,
        )

        assert handler._investment_repository == mock_investment_repository
        assert handler._unit_of_work == mock_unit_of_work

    async def test_handle_create_investment_success(
        self,
        handler,
        create_investment_command,
        mock_investment_repository,
        mock_unit_of_work,
    ):
        """Test création d'investissement réussie"""
        # Act
        result = await handler.handle(create_investment_command)

        # Assert
        assert isinstance(result, UUID)

        # Vérification des appels
        mock_investment_repository.save.assert_called_once()
        mock_unit_of_work.commit.assert_called_once()

        # Vérification des données passées au repository
        call_args = mock_investment_repository.save.call_args[0][0]
        assert call_args["symbol"] == "AAPL"
        assert call_args["name"] == "Apple Inc."
        assert call_args["investment_type"] == "Stock"
        assert call_args["sector"] == "Technology"

    async def test_handle_create_investment_with_optional_fields(
        self, handler, mock_investment_repository, mock_unit_of_work
    ):
        """Test création d'investissement sans ISIN (champ optionnel)"""
        command = CreateInvestmentCommand(
            symbol="GOOGL",
            name="Alphabet Inc.",
            investment_type="Stock",
            sector="Technology",
            market_cap="Large Cap",
            currency="USD",
            exchange="NASDAQ",
            isin=None,
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert isinstance(result, UUID)

        call_args = mock_investment_repository.save.call_args[0][0]
        assert call_args["isin"] is None

    async def test_handle_repository_error(
        self, handler, create_investment_command, mock_investment_repository
    ):
        """Test gestion d'erreur du repository"""
        mock_investment_repository.save.side_effect = Exception("Database error")

        # Act & Assert
        with pytest.raises(Exception, match="Database error"):
            await handler.handle(create_investment_command)

    async def test_handle_unit_of_work_integration(
        self, handler, create_investment_command, mock_unit_of_work
    ):
        """Test intégration avec unit of work"""
        # Act
        await handler.handle(create_investment_command)

        # Assert
        mock_unit_of_work.__aenter__.assert_called_once()
        mock_unit_of_work.__aexit__.assert_called_once()
        mock_unit_of_work.commit.assert_called_once()


class TestCreatePortfolioCommandHandler:
    """Tests pour CreatePortfolioCommandHandler"""

    @pytest.fixture
    def mock_portfolio_repository(self):
        return AsyncMock()

    @pytest.fixture
    def mock_user_repository(self):
        return AsyncMock()

    @pytest.fixture
    def mock_unit_of_work(self):
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        return mock_uow

    @pytest.fixture
    def handler(
        self, mock_portfolio_repository, mock_user_repository, mock_unit_of_work
    ):
        return CreatePortfolioCommandHandler(
            portfolio_repository=mock_portfolio_repository,
            user_repository=mock_user_repository,
            unit_of_work=mock_unit_of_work,
        )

    @pytest.fixture
    def create_portfolio_command(self):
        return CreatePortfolioCommand(
            user_id=uuid4(),
            name="My Portfolio",
            description="Test portfolio",
            initial_cash_amount=10000.0,
            currency="USD",
        )

    @pytest.fixture
    def mock_user(self):
        user = MagicMock()
        user.id = uuid4()
        return user

    def test_handler_initialization(
        self, mock_portfolio_repository, mock_user_repository, mock_unit_of_work
    ):
        """Test l'initialisation du handler"""
        handler = CreatePortfolioCommandHandler(
            portfolio_repository=mock_portfolio_repository,
            user_repository=mock_user_repository,
            unit_of_work=mock_unit_of_work,
        )

        assert handler._portfolio_repository == mock_portfolio_repository
        assert handler._user_repository == mock_user_repository
        assert handler._unit_of_work == mock_unit_of_work

    async def test_handle_create_portfolio_success(
        self,
        handler,
        create_portfolio_command,
        mock_user,
        mock_portfolio_repository,
        mock_user_repository,
        mock_unit_of_work,
    ):
        """Test création de portfolio réussie"""
        # Arrange
        mock_user_repository.find_by_id.return_value = mock_user

        # Act
        result = await handler.handle(create_portfolio_command)

        # Assert
        assert isinstance(result, UUID)

        # Vérifications des appels
        mock_user_repository.find_by_id.assert_called_once_with(
            create_portfolio_command.user_id
        )
        mock_portfolio_repository.save.assert_called_once()
        mock_unit_of_work.commit.assert_called_once()

        # Vérification des données du portfolio
        call_args = mock_portfolio_repository.save.call_args[0][0]
        assert call_args["user_id"] == create_portfolio_command.user_id
        assert call_args["name"] == "My Portfolio"
        assert call_args["description"] == "Test portfolio"
        assert abs(call_args["cash_balance"]["amount"] - 10000.0) < 0.01
        assert call_args["cash_balance"]["currency"] == "USD"

    async def test_handle_user_not_found(
        self, handler, create_portfolio_command, mock_user_repository
    ):
        """Test erreur utilisateur non trouvé"""
        # Arrange
        mock_user_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="User .+ not found"):
            await handler.handle(create_portfolio_command)

        # Vérification qu'on n'a pas tenté de sauvegarder
        mock_user_repository.find_by_id.assert_called_once()

    async def test_handle_create_portfolio_minimal_data(
        self,
        mock_portfolio_repository,
        mock_user_repository,
        mock_unit_of_work,
        mock_user,
    ):
        """Test création de portfolio avec données minimales"""
        handler = CreatePortfolioCommandHandler(
            portfolio_repository=mock_portfolio_repository,
            user_repository=mock_user_repository,
            unit_of_work=mock_unit_of_work,
        )

        command = CreatePortfolioCommand(user_id=uuid4(), name="Simple Portfolio")

        # Arrange
        mock_user_repository.find_by_id.return_value = mock_user

        # Act
        result = await handler.handle(command)

        # Assert
        assert isinstance(result, UUID)

        call_args = mock_portfolio_repository.save.call_args[0][0]
        assert call_args["description"] is None
        assert abs(call_args["cash_balance"]["amount"] - 0.0) < 0.01
        assert call_args["cash_balance"]["currency"] == "USD"


class TestAddInvestmentToPortfolioCommandHandler:
    """Tests pour AddInvestmentToPortfolioCommandHandler"""

    @pytest.fixture
    def mock_portfolio_repository(self):
        return AsyncMock()

    @pytest.fixture
    def mock_investment_repository(self):
        return AsyncMock()

    @pytest.fixture
    def mock_unit_of_work(self):
        mock_uow = AsyncMock()
        mock_uow.__aenter__ = AsyncMock(return_value=mock_uow)
        mock_uow.__aexit__ = AsyncMock(return_value=None)
        return mock_uow

    @pytest.fixture
    def handler(
        self, mock_portfolio_repository, mock_investment_repository, mock_unit_of_work
    ):
        return AddInvestmentToPortfolioCommandHandler(
            portfolio_repository=mock_portfolio_repository,
            investment_repository=mock_investment_repository,
            unit_of_work=mock_unit_of_work,
        )

    @pytest.fixture
    def add_investment_command(self):
        return AddInvestmentToPortfolioCommand(
            portfolio_id=uuid4(),
            investment_id=uuid4(),
            quantity=10,
            purchase_price=150.0,
            currency="USD",
        )

    @pytest.fixture
    def mock_portfolio(self):
        portfolio = MagicMock()
        portfolio.id = uuid4()
        portfolio.cash_balance = MagicMock()
        portfolio.cash_balance.amount = 2000.0
        portfolio.add_investment = MagicMock()
        return portfolio

    @pytest.fixture
    def mock_investment(self):
        investment = MagicMock()
        investment.id = uuid4()
        investment.symbol = "AAPL"
        return investment

    def test_handler_initialization(
        self, mock_portfolio_repository, mock_investment_repository, mock_unit_of_work
    ):
        """Test l'initialisation du handler"""
        handler = AddInvestmentToPortfolioCommandHandler(
            portfolio_repository=mock_portfolio_repository,
            investment_repository=mock_investment_repository,
            unit_of_work=mock_unit_of_work,
        )

        assert handler._portfolio_repository == mock_portfolio_repository
        assert handler._investment_repository == mock_investment_repository
        assert handler._unit_of_work == mock_unit_of_work

    async def test_handle_add_investment_success(
        self,
        handler,
        add_investment_command,
        mock_portfolio,
        mock_investment,
        mock_portfolio_repository,
        mock_investment_repository,
        mock_unit_of_work,
    ):
        """Test ajout d'investissement réussi"""
        # Arrange
        mock_portfolio_repository.find_by_id.return_value = mock_portfolio
        mock_investment_repository.find_by_id.return_value = mock_investment

        # Act
        result = await handler.handle(add_investment_command)

        # Assert
        assert result is True

        # Vérifications des appels
        mock_portfolio_repository.find_by_id.assert_called_once_with(
            add_investment_command.portfolio_id
        )
        mock_investment_repository.find_by_id.assert_called_once_with(
            add_investment_command.investment_id
        )
        mock_portfolio.add_investment.assert_called_once_with(
            mock_investment, 10, 150.0
        )
        mock_portfolio_repository.save.assert_called_once_with(mock_portfolio)
        mock_unit_of_work.commit.assert_called_once()

    async def test_handle_portfolio_not_found(
        self, handler, add_investment_command, mock_portfolio_repository
    ):
        """Test erreur portfolio non trouvé"""
        # Arrange
        mock_portfolio_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Portfolio .+ not found"):
            await handler.handle(add_investment_command)

    async def test_handle_investment_not_found(
        self,
        handler,
        add_investment_command,
        mock_portfolio,
        mock_portfolio_repository,
        mock_investment_repository,
    ):
        """Test erreur investissement non trouvé"""
        # Arrange
        mock_portfolio_repository.find_by_id.return_value = mock_portfolio
        mock_investment_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Investment .+ not found"):
            await handler.handle(add_investment_command)

    async def test_handle_insufficient_cash_balance(
        self,
        handler,
        mock_portfolio,
        mock_investment,
        mock_portfolio_repository,
        mock_investment_repository,
    ):
        """Test erreur solde insuffisant"""
        # Arrange - Portfolio avec solde insuffisant
        mock_portfolio.cash_balance.amount = 100.0  # Moins que 10 * 150.0 = 1500.0
        mock_portfolio_repository.find_by_id.return_value = mock_portfolio
        mock_investment_repository.find_by_id.return_value = mock_investment

        command = AddInvestmentToPortfolioCommand(
            portfolio_id=uuid4(),
            investment_id=uuid4(),
            quantity=10,
            purchase_price=150.0,
            currency="USD",
        )

        # Act & Assert
        with pytest.raises(ValueError, match="Insufficient cash balance"):
            await handler.handle(command)

    async def test_handle_edge_case_exact_cash_balance(
        self,
        handler,
        mock_portfolio,
        mock_investment,
        mock_portfolio_repository,
        mock_investment_repository,
        mock_unit_of_work,
    ):
        """Test cas limite avec solde exact"""
        # Arrange - Portfolio avec solde exact
        mock_portfolio.cash_balance.amount = 1500.0  # Exactement 10 * 150.0 = 1500.0
        mock_portfolio_repository.find_by_id.return_value = mock_portfolio
        mock_investment_repository.find_by_id.return_value = mock_investment

        command = AddInvestmentToPortfolioCommand(
            portfolio_id=uuid4(),
            investment_id=uuid4(),
            quantity=10,
            purchase_price=150.0,
            currency="USD",
        )

        # Act
        result = await handler.handle(command)

        # Assert
        assert result is True


class TestGenerateSignalCommandHandler:
    """Tests pour GenerateSignalCommandHandler"""

    @pytest.fixture
    def mock_signal_generator(self):
        return AsyncMock()

    @pytest.fixture
    def handler(self, mock_signal_generator):
        return GenerateSignalCommandHandler(signal_generator=mock_signal_generator)

    @pytest.fixture
    def generate_signal_command(self):
        return GenerateSignalCommand(investment_id=uuid4())

    @pytest.fixture
    def mock_signal(self):
        signal = MagicMock()
        signal.timestamp = "2024-01-01T10:00:00Z"
        signal.signal_type = "BUY"
        signal.strength = 0.8
        return signal

    def test_handler_initialization(self, mock_signal_generator):
        """Test l'initialisation du handler"""
        handler = GenerateSignalCommandHandler(signal_generator=mock_signal_generator)

        assert handler._signal_generator == mock_signal_generator

    async def test_handle_generate_signal_success(
        self,
        handler,
        generate_signal_command,
        mock_signal,
        mock_signal_generator,
    ):
        """Test génération de signal réussie"""
        # Arrange
        mock_signal_generator.generate_signal.return_value = mock_signal

        # Act
        result = await handler.handle(generate_signal_command)

        # Assert
        assert isinstance(result, dict)
        assert result["investment_id"] == generate_signal_command.investment_id
        assert result["signal"] == mock_signal
        assert result["generated_at"] == "2024-01-01T10:00:00Z"

        # Vérification de l'appel au service
        mock_signal_generator.generate_signal.assert_called_once_with("PLACEHOLDER")

    async def test_handle_signal_generation_error(
        self, handler, generate_signal_command, mock_signal_generator
    ):
        """Test gestion d'erreur lors de la génération de signal"""
        # Arrange
        mock_signal_generator.generate_signal.side_effect = Exception(
            "Signal generation failed"
        )

        # Act & Assert
        with pytest.raises(Exception, match="Signal generation failed"):
            await handler.handle(generate_signal_command)


class TestCommandHandlersIntegration:
    """Tests d'intégration entre les command handlers"""

    def test_all_handlers_implement_required_interface(self):
        """Test que tous les handlers implémentent l'interface requise"""
        handlers = [
            CreateInvestmentCommandHandler,
            CreatePortfolioCommandHandler,
            AddInvestmentToPortfolioCommandHandler,
            GenerateSignalCommandHandler,
        ]

        for handler_class in handlers:
            assert hasattr(
                handler_class, "handle"
            ), f"{handler_class.__name__} must have handle method"

    def test_handlers_dependency_injection(self):
        """Test l'injection de dépendances dans tous les handlers"""
        # Test avec mocks
        mock_repo = AsyncMock()
        mock_uow = AsyncMock()
        mock_signal_gen = AsyncMock()

        # Création de tous les handlers
        create_investment_handler = CreateInvestmentCommandHandler(mock_repo, mock_uow)
        create_portfolio_handler = CreatePortfolioCommandHandler(
            mock_repo, mock_repo, mock_uow
        )
        add_investment_handler = AddInvestmentToPortfolioCommandHandler(
            mock_repo, mock_repo, mock_uow
        )
        signal_handler = GenerateSignalCommandHandler(mock_signal_gen)

        # Vérification de l'injection
        assert create_investment_handler._investment_repository is mock_repo
        assert create_portfolio_handler._portfolio_repository is mock_repo
        assert add_investment_handler._portfolio_repository is mock_repo
        assert signal_handler._signal_generator is mock_signal_gen

    def test_command_handlers_async_compatibility(self):
        """Test que tous les handlers sont compatibles async"""
        import inspect

        handlers = [
            CreateInvestmentCommandHandler,
            CreatePortfolioCommandHandler,
            AddInvestmentToPortfolioCommandHandler,
            GenerateSignalCommandHandler,
        ]

        for handler_class in handlers:
            handle_method = getattr(handler_class, "handle")
            assert inspect.iscoroutinefunction(
                handle_method
            ), f"{handler_class.__name__}.handle must be async"
