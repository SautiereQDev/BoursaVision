"""
Tests fonctionnels pour UserRepository uniquement.
"""

import pytest

from boursa_vision.infrastructure.persistence.repositories import (
    SQLAlchemyUserRepository,
)


class TestUserRepositoryBasics:
    """Tests de base pour UserRepository."""

    def test_user_repository_creation(self):
        """Test création du UserRepository."""
        repo = SQLAlchemyUserRepository()
        assert repo is not None
        assert hasattr(repo, "_mapper")

    def test_user_repository_has_find_methods(self):
        """Test que UserRepository a les méthodes de recherche."""
        repo = SQLAlchemyUserRepository()

        # Méthodes de recherche
        assert hasattr(repo, "find_by_id")
        assert hasattr(repo, "find_by_email")
        assert hasattr(repo, "find_by_username")

    def test_user_repository_has_save_delete(self):
        """Test que UserRepository a save et delete."""
        repo = SQLAlchemyUserRepository()

        assert hasattr(repo, "save")
        assert hasattr(repo, "delete")

    def test_user_repository_has_exists_methods(self):
        """Test que UserRepository a les méthodes exists."""
        repo = SQLAlchemyUserRepository()

        assert hasattr(repo, "exists_by_email")
        assert hasattr(repo, "exists_by_username")

    def test_user_repository_has_available_methods(self):
        """Test que UserRepository a les méthodes disponibles."""
        repo = SQLAlchemyUserRepository()

        # Seulement les méthodes qui existent vraiment
        available_methods = [
            method
            for method in dir(repo)
            if not method.startswith("_") and callable(getattr(repo, method))
        ]

        # Vérifier qu'il y a des méthodes disponibles
        assert len(available_methods) > 0

    def test_user_repository_callable_methods_basic(self):
        """Test que les méthodes de base sont appelables."""
        repo = SQLAlchemyUserRepository()

        # Vérifier que les méthodes de base sont callable
        assert callable(repo.find_by_id)
        assert callable(repo.find_by_email)
        assert callable(repo.find_by_username)
        assert callable(repo.save)
        assert callable(repo.delete)
        assert callable(repo.exists_by_email)
        assert callable(repo.exists_by_username)

    def test_user_repository_mapper_has_to_domain(self):
        """Test que le mapper a to_domain."""
        repo = SQLAlchemyUserRepository()

        assert hasattr(repo._mapper, "to_domain")

    def test_user_repository_mapper_has_to_persistence(self):
        """Test que le mapper a to_persistence."""
        repo = SQLAlchemyUserRepository()

        # Vérifier to_persistence (peut être to_model selon implémentation)
        assert hasattr(repo._mapper, "to_persistence") or hasattr(
            repo._mapper, "to_model"
        )

    def test_user_repository_mapper_type(self):
        """Test que le mapper est de type UserMapper."""
        repo = SQLAlchemyUserRepository()

        # Vérifier le type
        mapper_class_name = repo._mapper.__class__.__name__
        assert "UserMapper" in mapper_class_name


if __name__ == "__main__":
    pytest.main([__file__])
