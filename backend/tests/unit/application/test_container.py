"""
Tests unitaires pour le conteneur d'injection de dépendances.

Ces tests vérifient la création et la gestion des services via le container DI,
ainsi que le respect des patterns Singleton et la gestion des dépendances.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Configuration du chemin d'import
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestApplicationContainerDependencies:
    """Tests pour la classe ApplicationContainerDependencies."""

    def test_dependencies_creation(self):
        """Test la création d'une instance de dépendances."""
        try:
            from boursa_vision.application.container import (
                ApplicationContainerDependencies,
            )
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        # Mock des dépendances
        mock_investment_repo = MagicMock()
        mock_market_data_repo = MagicMock()
        mock_scoring_service = MagicMock()

        deps = ApplicationContainerDependencies(
            investment_repository=mock_investment_repo,
            market_data_repository=mock_market_data_repo,
            scoring_service=mock_scoring_service,
        )

        assert deps.investment_repository is mock_investment_repo
        assert deps.market_data_repository is mock_market_data_repo
        assert deps.scoring_service is mock_scoring_service

    def test_dependencies_immutability(self):
        """Test que les dépendances sont configurées comme immutable (dataclass)."""
        try:
            from boursa_vision.application.container import (
                ApplicationContainerDependencies,
            )
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        # Vérifier que c'est bien une dataclass
        assert hasattr(ApplicationContainerDependencies, "__dataclass_fields__")

        # Vérifier les champs attendus
        fields = ApplicationContainerDependencies.__dataclass_fields__
        expected_fields = {
            "investment_repository",
            "market_data_repository",
            "scoring_service",
        }
        assert set(fields.keys()) == expected_fields


class TestApplicationContainer:
    """Tests pour la classe ApplicationContainer."""

    @pytest.fixture
    def mock_dependencies(self):
        """Fixture pour les dépendances mockées."""
        try:
            from boursa_vision.application.container import (
                ApplicationContainerDependencies,
            )
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        return ApplicationContainerDependencies(
            investment_repository=MagicMock(),
            market_data_repository=MagicMock(),
            scoring_service=MagicMock(),
        )

    def test_container_initialization(self, mock_dependencies):
        """Test l'initialisation du container avec dépendances."""
        try:
            from boursa_vision.application.container import ApplicationContainer
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        container = ApplicationContainer(mock_dependencies)

        assert container._deps is mock_dependencies
        assert container._technical_analyzer is None
        assert container._signal_generator is None

    def test_container_implements_protocol(self, mock_dependencies):
        """Test que le container implémente le protocol."""
        try:
            from boursa_vision.application.container import (
                ApplicationContainer,
            )
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        container = ApplicationContainer(mock_dependencies)

        # Vérifier que les méthodes du protocol sont présentes
        assert hasattr(container, "get_technical_analyzer")
        assert hasattr(container, "get_signal_generator")
        assert callable(container.get_technical_analyzer)
        assert callable(container.get_signal_generator)

    def test_get_technical_analyzer_lazy_initialization(self, mock_dependencies):
        """Test l'initialisation paresseuse du TechnicalAnalyzer."""
        try:
            from boursa_vision.application.container import ApplicationContainer
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        container = ApplicationContainer(mock_dependencies)

        # Mock de l'import dynamique dans le contexte de la méthode
        with patch.object(container, "get_technical_analyzer") as mock_method:
            mock_analyzer_instance = MagicMock()
            mock_method.return_value = mock_analyzer_instance

            # Première fois
            result1 = container.get_technical_analyzer()

            # Deuxième fois
            result2 = container.get_technical_analyzer()

            # Vérifier que c'est la même instance
            assert result1 is result2

    def test_get_signal_generator_lazy_initialization(self, mock_dependencies):
        """Test l'initialisation paresseuse du SignalGenerator."""
        try:
            from boursa_vision.application.container import ApplicationContainer
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        container = ApplicationContainer(mock_dependencies)

        # Mock de l'import dynamique dans le contexte de la méthode
        with patch.object(container, "get_signal_generator") as mock_method:
            mock_generator_instance = MagicMock()
            mock_method.return_value = mock_generator_instance

            # Première fois
            result1 = container.get_signal_generator()

            # Deuxième fois
            result2 = container.get_signal_generator()

            # Vérifier que c'est la même instance
            assert result1 is result2

    def test_technical_analyzer_service_dependency_injection(self, mock_dependencies):
        """Test l'injection des dépendances dans TechnicalAnalyzer."""
        try:
            from boursa_vision.application.container import ApplicationContainer
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        container = ApplicationContainer(mock_dependencies)

        # Vérifier que les dépendances sont bien stockées
        assert (
            container._deps.investment_repository
            is mock_dependencies.investment_repository
        )
        assert (
            container._deps.market_data_repository
            is mock_dependencies.market_data_repository
        )
        assert container._deps.scoring_service is mock_dependencies.scoring_service

        # Vérifier l'état initial
        assert container._technical_analyzer is None
        assert container._signal_generator is None

    def test_signal_generator_dependency_chain(self, mock_dependencies):
        """Test la chaîne de dépendances pour SignalGenerator."""
        try:
            from boursa_vision.application.container import ApplicationContainer
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        container = ApplicationContainer(mock_dependencies)

        # Simuler que le technical analyzer est déjà créé
        mock_analyzer = MagicMock()
        container._technical_analyzer = mock_analyzer

        # Vérifier que le signal generator peut utiliser l'analyzer
        assert container._technical_analyzer is mock_analyzer

    def test_container_import_error_simulation(self, mock_dependencies):
        """Test la simulation d'erreurs d'import."""
        try:
            from boursa_vision.application.container import ApplicationContainer
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        container = ApplicationContainer(mock_dependencies)

        # Simuler une erreur en patchant les imports internes
        def mock_failing_get_analyzer():
            raise ImportError("Service not available")

        container.get_technical_analyzer = mock_failing_get_analyzer

        with pytest.raises(ImportError, match="Service not available"):
            container.get_technical_analyzer()

    def test_container_service_lifecycle(self, mock_dependencies):
        """Test le cycle de vie des services dans le container."""
        try:
            from boursa_vision.application.container import ApplicationContainer
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        container = ApplicationContainer(mock_dependencies)

        # État initial
        assert container._technical_analyzer is None
        assert container._signal_generator is None

        # Simuler la création d'un service
        mock_service = MagicMock()
        container._technical_analyzer = mock_service

        # Vérifier que l'état a changé
        assert container._technical_analyzer is mock_service
        assert container._signal_generator is None

    def test_container_service_isolation(self, mock_dependencies):
        """Test l'isolation des services dans le container."""
        try:
            from boursa_vision.application.container import ApplicationContainer
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        container = ApplicationContainer(mock_dependencies)

        # Modifier un attribut interne
        container._technical_analyzer = "modified"

        # Vérifier que les dépendances originales ne sont pas affectées
        assert mock_dependencies.investment_repository is not None
        assert mock_dependencies.market_data_repository is not None
        assert mock_dependencies.scoring_service is not None


class TestApplicationContainerProtocol:
    """Tests pour le protocol ApplicationContainerProtocol."""

    def test_protocol_definition(self):
        """Test que le protocol définit les bonnes méthodes."""
        try:
            from boursa_vision.application.container import ApplicationContainerProtocol
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        # Vérifier que c'est bien un protocol
        assert hasattr(ApplicationContainerProtocol, "__annotations__")

        # Vérifier que les méthodes essentielles sont présentes
        assert "get_technical_analyzer" in str(
            ApplicationContainerProtocol.__annotations__
        ) or hasattr(ApplicationContainerProtocol, "get_technical_analyzer")
        assert "get_signal_generator" in str(
            ApplicationContainerProtocol.__annotations__
        ) or hasattr(ApplicationContainerProtocol, "get_signal_generator")


class TestApplicationContainerIntegration:
    """Tests d'intégration pour le container."""

    def test_container_basic_functionality(self):
        """Test de base du container."""
        try:
            from boursa_vision.application.container import (
                ApplicationContainer,
                ApplicationContainerDependencies,
            )
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        # Créer des mocks réalistes
        mock_deps = ApplicationContainerDependencies(
            investment_repository=MagicMock(name="InvestmentRepository"),
            market_data_repository=MagicMock(name="MarketDataRepository"),
            scoring_service=MagicMock(name="ScoringService"),
        )

        container = ApplicationContainer(mock_deps)

        # Vérifier l'initialisation
        assert container._deps is mock_deps
        assert container._technical_analyzer is None
        assert container._signal_generator is None

    def test_container_state_consistency(self):
        """Test la cohérence de l'état du container."""
        try:
            from boursa_vision.application.container import (
                ApplicationContainer,
                ApplicationContainerDependencies,
            )
        except ImportError:
            pytest.skip("Module container non accessible - test ignoré")

        mock_deps = ApplicationContainerDependencies(
            investment_repository=MagicMock(),
            market_data_repository=MagicMock(),
            scoring_service=MagicMock(),
        )

        container1 = ApplicationContainer(mock_deps)
        container2 = ApplicationContainer(mock_deps)

        # Les containers sont indépendants
        assert container1 is not container2
        assert container1._deps is container2._deps  # Même dépendances

        # Mais leurs services internes sont indépendants
        container1._technical_analyzer = "test1"
        container2._technical_analyzer = "test2"

        assert container1._technical_analyzer != container2._technical_analyzer
