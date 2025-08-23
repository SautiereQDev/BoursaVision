"""
Tests unitaires simples pour les repositories.

Phase 1 : Tests basiques pour améliorer le coverage des repositories
sans connexion réelle à la base de données.
"""

import pytest


@pytest.mark.unit
class TestRepositoriesImport:
    """Tests d'import des repositories."""

    def test_sqlalchemy_user_repository_import_succeeds(self):
        """L'import de SQLAlchemyUserRepository devrait réussir."""
        # Act & Assert
        try:
            from boursa_vision.infrastructure.persistence import (
                SQLAlchemyUserRepository,
            )

            assert SQLAlchemyUserRepository is not None
        except ImportError as e:
            pytest.fail(f"Failed to import SQLAlchemyUserRepository: {e}")

    def test_sqlalchemy_portfolio_repository_import_succeeds(self):
        """L'import de SQLAlchemyPortfolioRepository devrait réussir."""
        # Act & Assert
        try:
            from boursa_vision.infrastructure.persistence import (
                SQLAlchemyPortfolioRepository,
            )

            assert SQLAlchemyPortfolioRepository is not None
        except ImportError as e:
            pytest.fail(f"Failed to import SQLAlchemyPortfolioRepository: {e}")

    def test_sqlalchemy_market_data_repository_import_succeeds(self):
        """L'import de SQLAlchemyMarketDataRepository devrait réussir."""
        # Act & Assert
        try:
            from boursa_vision.infrastructure.persistence import (
                SQLAlchemyMarketDataRepository,
            )

            assert SQLAlchemyMarketDataRepository is not None
        except ImportError as e:
            pytest.fail(f"Failed to import SQLAlchemyMarketDataRepository: {e}")

    def test_repositories_module_import_succeeds(self):
        """L'import du module repositories devrait réussir."""
        # Act & Assert
        try:
            from boursa_vision.infrastructure.persistence import repositories

            # Les classes sont bien là mais avec les bons noms
            assert repositories is not None
        except ImportError as e:
            pytest.fail(f"Failed to import repositories module: {e}")


@pytest.mark.unit
class TestRepositoriesMethods:
    """Tests de base sur les méthodes des repositories."""

    def test_user_repository_has_basic_methods(self):
        """SQLAlchemyUserRepository a des méthodes de base."""
        # Arrange
        from boursa_vision.infrastructure.persistence import SQLAlchemyUserRepository

        # Act & Assert
        # Test seulement les méthodes qui existent réellement
        basic_methods = ["find_by_id", "find_by_email"]
        for method_name in basic_methods:
            assert hasattr(
                SQLAlchemyUserRepository, method_name
            ), f"Missing method: {method_name}"

    def test_portfolio_repository_has_basic_methods(self):
        """SQLAlchemyPortfolioRepository a des méthodes de base."""
        # Arrange
        from boursa_vision.infrastructure.persistence import (
            SQLAlchemyPortfolioRepository,
        )

        # Act & Assert
        # Test seulement les méthodes qui existent réellement
        basic_methods = ["find_by_id", "find_by_user_id"]
        for method_name in basic_methods:
            assert hasattr(
                SQLAlchemyPortfolioRepository, method_name
            ), f"Missing method: {method_name}"

    def test_market_data_repository_has_basic_methods(self):
        """SQLAlchemyMarketDataRepository a des méthodes de base."""
        # Arrange
        from boursa_vision.infrastructure.persistence import (
            SQLAlchemyMarketDataRepository,
        )

        # Act & Assert
        # Test seulement les méthodes qui existent réellement
        basic_methods = ["find_latest_by_symbol", "find_by_symbol"]
        for method_name in basic_methods:
            assert hasattr(
                SQLAlchemyMarketDataRepository, method_name
            ), f"Missing method: {method_name}"


@pytest.mark.unit
class TestRepositoriesStructure:
    """Tests sur la structure des classes de repositories."""

    def test_user_repository_is_class(self):
        """SQLAlchemyUserRepository est une classe."""
        # Arrange
        from boursa_vision.infrastructure.persistence import SQLAlchemyUserRepository

        # Act & Assert
        assert isinstance(SQLAlchemyUserRepository, type)
        assert SQLAlchemyUserRepository.__name__ == "SQLAlchemyUserRepository"

    def test_portfolio_repository_is_class(self):
        """SQLAlchemyPortfolioRepository est une classe."""
        # Arrange
        from boursa_vision.infrastructure.persistence import (
            SQLAlchemyPortfolioRepository,
        )

        # Act & Assert
        assert isinstance(SQLAlchemyPortfolioRepository, type)
        assert SQLAlchemyPortfolioRepository.__name__ == "SQLAlchemyPortfolioRepository"

    def test_market_data_repository_is_class(self):
        """SQLAlchemyMarketDataRepository est une classe."""
        # Arrange
        from boursa_vision.infrastructure.persistence import (
            SQLAlchemyMarketDataRepository,
        )

        # Act & Assert
        assert isinstance(SQLAlchemyMarketDataRepository, type)
        assert (
            SQLAlchemyMarketDataRepository.__name__ == "SQLAlchemyMarketDataRepository"
        )

    def test_repositories_have_docstrings(self):
        """Les classes de repositories ont des docstrings."""
        # Arrange
        from boursa_vision.infrastructure.persistence import (
            SQLAlchemyMarketDataRepository,
            SQLAlchemyPortfolioRepository,
            SQLAlchemyUserRepository,
        )

        # Act & Assert
        for repo_class in [
            SQLAlchemyUserRepository,
            SQLAlchemyPortfolioRepository,
            SQLAlchemyMarketDataRepository,
        ]:
            assert repo_class.__doc__ is not None
            assert len(repo_class.__doc__.strip()) > 0


@pytest.mark.unit
class TestRepositoriesBasicCallability:
    """Tests de base sur l'appelabilité des méthodes."""

    def test_repository_methods_are_callable(self):
        """Les méthodes des repositories sont appelables."""
        # Arrange
        from boursa_vision.infrastructure.persistence import (
            SQLAlchemyMarketDataRepository,
            SQLAlchemyPortfolioRepository,
            SQLAlchemyUserRepository,
        )

        # Act & Assert
        user_methods = ["find_by_id", "find_by_email"]
        for method_name in user_methods:
            method = getattr(SQLAlchemyUserRepository, method_name)
            assert callable(method)

        portfolio_methods = ["find_by_id", "find_by_user_id"]
        for method_name in portfolio_methods:
            method = getattr(SQLAlchemyPortfolioRepository, method_name)
            assert callable(method)

        market_data_methods = ["find_latest_by_symbol", "find_by_symbol"]
        for method_name in market_data_methods:
            method = getattr(SQLAlchemyMarketDataRepository, method_name)
            assert callable(method)
