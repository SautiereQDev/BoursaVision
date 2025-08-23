"""
Tests minimalistes pour les repositories - focus coverage réel.
"""

import pytest

from boursa_vision.infrastructure.persistence.repositories import (
    SQLAlchemyInvestmentRepository,
    SQLAlchemyUserRepository,
)


class TestRepositoryInstantiation:
    """Tests d'instanciation des repositories."""

    def test_user_repository_creation(self):
        """Test création du UserRepository."""
        repo = SQLAlchemyUserRepository()
        assert repo is not None
        assert hasattr(repo, "_mapper")

    def test_investment_repository_creation(self):
        """Test création du InvestmentRepository."""
        repo = SQLAlchemyInvestmentRepository()
        assert repo is not None
        assert hasattr(repo, "_mapper")


class TestRepositoryMethods:
    """Tests des méthodes publiques des repositories."""

    def test_user_repository_has_required_methods(self):
        """Test que UserRepository a les méthodes requises."""
        repo = SQLAlchemyUserRepository()

        # Vérifier les méthodes publiques
        assert hasattr(repo, "find_by_id")
        assert hasattr(repo, "find_by_email")
        assert hasattr(repo, "find_by_username")
        assert hasattr(repo, "save")
        assert hasattr(repo, "delete")
        assert hasattr(repo, "exists_by_email")
        assert hasattr(repo, "exists_by_username")
        assert hasattr(repo, "find_all_active")
        assert hasattr(repo, "count_active")

    def test_investment_repository_has_required_methods(self):
        """Test que InvestmentRepository a les méthodes requises."""
        repo = SQLAlchemyInvestmentRepository()

        # Vérifier les méthodes publiques
        assert hasattr(repo, "find_by_id")
        assert hasattr(repo, "find_by_portfolio_id")
        assert hasattr(repo, "save")
        assert hasattr(repo, "delete")
        assert hasattr(repo, "exists")
        assert hasattr(repo, "find_all")


class TestRepositoryMappers:
    """Tests des mappers des repositories."""

    def test_user_repository_mapper_initialization(self):
        """Test l'initialisation du mapper UserRepository."""
        repo = SQLAlchemyUserRepository()

        # Vérifier le mapper
        assert repo._mapper is not None

        # Vérifier les méthodes du mapper
        assert hasattr(repo._mapper, "to_domain")
        assert hasattr(repo._mapper, "to_model")

    def test_investment_repository_mapper_initialization(self):
        """Test l'initialisation du mapper InvestmentRepository."""
        repo = SQLAlchemyInvestmentRepository()

        # Vérifier le mapper
        assert repo._mapper is not None

        # Vérifier les méthodes du mapper
        assert hasattr(repo._mapper, "to_domain")
        assert hasattr(repo._mapper, "to_model")


if __name__ == "__main__":
    pytest.main([__file__])
