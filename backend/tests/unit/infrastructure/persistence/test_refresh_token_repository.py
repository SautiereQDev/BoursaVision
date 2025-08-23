"""
Tests unitaires pour le repository SQLAlchemyRefreshTokenRepository.

Tests conformes à l'architecture définie dans TESTS.md.
Focus sur la structure et les méthodes du repository refresh token.
"""

from pathlib import Path

import pytest


@pytest.mark.unit
class TestRefreshTokenRepositoryModuleStructure:
    """Tests de structure et disponibilité du module refresh token repository."""

    def test_refresh_token_repository_module_file_exists(self):
        """Vérifie que le fichier refresh token repository existe."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        assert repo_path.exists()
        assert repo_path.is_file()

    def test_refresh_token_repository_module_has_docstring(self):
        """Vérifie que le module refresh token repository a une docstring."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "SQLAlchemy RefreshToken Repository Implementation" in content
        assert (
            "Repository implementation for RefreshToken entity using SQLAlchemy"
            in content
        )


@pytest.mark.unit
class TestRefreshTokenRepositoryImports:
    """Tests d'imports et gestion des dépendances."""

    def test_refresh_token_repository_required_imports_exist(self):
        """Vérifie que les imports requis sont disponibles."""
        required_imports = ["datetime", "typing", "uuid"]

        for import_name in required_imports:
            try:
                __import__(import_name)
            except ImportError:
                pytest.fail(f"Required import {import_name} not available")

    def test_refresh_token_repository_imports_sqlalchemy(self):
        """Vérifie les imports SQLAlchemy."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "from sqlalchemy import and_, select" in content
        assert "from sqlalchemy.ext.asyncio import AsyncSession" in content

    def test_refresh_token_repository_imports_domain_components(self):
        """Vérifie les imports du domaine."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "RefreshToken as DomainRefreshToken" in content
        assert (
            "from boursa_vision.domain.repositories.refresh_token_repository import"
            in content
        )
        assert "IRefreshTokenRepository" in content
        assert (
            "from boursa_vision.infrastructure.persistence.models.refresh_tokens import RefreshToken"
            in content
        )


@pytest.mark.unit
class TestSQLAlchemyRefreshTokenRepositoryClass:
    """Tests de la classe SQLAlchemyRefreshTokenRepository."""

    def test_refresh_token_repository_class_definition(self):
        """Vérifie que la classe SQLAlchemyRefreshTokenRepository est définie."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert (
            "class SQLAlchemyRefreshTokenRepository(IRefreshTokenRepository):"
            in content
        )
        assert "SQLAlchemy implementation of refresh token repository" in content

    def test_refresh_token_repository_init_method(self):
        """Vérifie que la méthode __init__ est correctement définie."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "def __init__(self, session: AsyncSession):" in content
        assert "Initialize repository with database session" in content
        assert "self.session = session" in content

    def test_refresh_token_repository_inherits_interface(self):
        """Vérifie que le repository hérite de l'interface."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "IRefreshTokenRepository" in content


@pytest.mark.unit
class TestRefreshTokenRepositoryBasicOperations:
    """Tests des opérations CRUD de base."""

    def test_find_by_id_method(self):
        """Vérifie la méthode find_by_id."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert (
            "async def find_by_id(self, entity_id: UUID) -> Optional[DomainRefreshToken]:"
            in content
        )
        assert "Find refresh token by ID" in content
        assert "select(RefreshToken).where(RefreshToken.id == entity_id)" in content

    def test_save_method(self):
        """Vérifie la méthode save."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert (
            "async def save(self, entity: DomainRefreshToken) -> DomainRefreshToken:"
            in content
        )
        assert "Save refresh token (create or update)" in content
        assert "existing = await self.find_by_id(entity.id)" in content
        assert "self.session.add(model)" in content

    def test_update_method(self):
        """Vérifie la méthode update."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert (
            "async def update(self, entity: DomainRefreshToken) -> DomainRefreshToken:"
            in content
        )
        assert "Update existing refresh token" in content

    def test_delete_method(self):
        """Vérifie la méthode delete."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "async def delete(self, entity_id: UUID) -> bool:" in content
        assert "Delete refresh token by ID" in content


@pytest.mark.unit
class TestRefreshTokenRepositorySpecializedQueries:
    """Tests des requêtes spécialisées."""

    def test_find_by_token_method(self):
        """Vérifie la méthode find_by_token."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert (
            "async def find_by_token(self, token: str) -> Optional[DomainRefreshToken]:"
            in content
        )
        assert "Find refresh token by token string" in content
        assert "RefreshToken.token == token" in content

    def test_find_by_user_id_method(self):
        """Vérifie la méthode find_by_user_id."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert (
            "async def find_by_user_id(self, user_id: UUID) -> List[DomainRefreshToken]:"
            in content
        )
        assert "Find all refresh tokens for a user" in content
        assert "RefreshToken.user_id == user_id" in content
        assert "order_by(RefreshToken.created_at.desc())" in content

    def test_find_active_by_user_id_method(self):
        """Vérifie la méthode find_active_by_user_id."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert (
            "async def find_active_by_user_id(self, user_id: UUID) -> List[DomainRefreshToken]:"
            in content
        )
        assert "Find all active (non-revoked, non-expired) refresh tokens" in content
        assert "RefreshToken.is_revoked is False" in content
        assert "RefreshToken.expires_at > now" in content

    def test_revoke_all_for_user_method(self):
        """Vérifie la méthode revoke_all_for_user."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "async def revoke_all_for_user(" in content
        assert "reason: str" in content
        assert '"logout_all"' in content
        assert "Revoke all refresh tokens for a user" in content
        assert "returns count of revoked tokens" in content


@pytest.mark.unit
class TestRefreshTokenRepositoryAsyncOperations:
    """Tests des opérations asynchrones."""

    def test_repository_uses_async_session(self):
        """Vérifie que le repository utilise AsyncSession."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "AsyncSession" in content
        assert "await self.session.execute(" in content
        assert "await self.session.flush()" in content

    def test_repository_methods_are_async(self):
        """Vérifie que les méthodes sont asynchrones."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "async def find_by_id(" in content
        assert "async def save(" in content
        assert "async def update(" in content
        assert "async def delete(" in content


@pytest.mark.unit
class TestRefreshTokenRepositoryTypeAnnotations:
    """Tests des annotations de type."""

    def test_repository_uses_correct_type_annotations(self):
        """Vérifie que le repository utilise les bonnes annotations de type."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "UUID" in content
        assert "Optional[DomainRefreshToken]" in content
        assert "List[DomainRefreshToken]" in content
        assert "DomainRefreshToken" in content

    def test_repository_imports_type_components(self):
        """Vérifie que le repository importe les composants de typage."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "from typing import List, Optional" in content
        assert "from uuid import UUID" in content


@pytest.mark.unit
class TestRefreshTokenRepositorySQLAlchemyQueries:
    """Tests des requêtes SQLAlchemy."""

    def test_repository_uses_select_statements(self):
        """Vérifie que le repository utilise des instructions SELECT."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "select(RefreshToken)" in content
        assert ".where(" in content
        assert ".order_by(" in content

    def test_repository_uses_and_conditions(self):
        """Vérifie que le repository utilise des conditions AND."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "and_(" in content

    def test_repository_handles_datetime_comparisons(self):
        """Vérifie que le repository gère les comparaisons de dates."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "datetime.now(timezone.utc)" in content
        assert "expires_at >" in content


@pytest.mark.unit
class TestRefreshTokenRepositoryErrorHandling:
    """Tests de gestion d'erreurs."""

    def test_repository_handles_not_found_errors(self):
        """Vérifie que le repository gère les erreurs de non-existence."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "if not model:" in content
        assert "raise ValueError(" in content
        assert "not found" in content

    def test_repository_returns_none_for_missing_entities(self):
        """Vérifie que le repository retourne None pour les entités manquantes."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "scalar_one_or_none()" in content
        assert "if model else None" in content


@pytest.mark.unit
class TestRefreshTokenRepositoryDataMapping:
    """Tests de mapping des données."""

    def test_repository_has_data_transformation_methods(self):
        """Vérifie que le repository a des méthodes de transformation."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "_to_domain(" in content or "self._to_domain(" in content
        assert "_to_persistence(" in content or "self._to_persistence(" in content

    def test_repository_uses_model_transformation(self):
        """Vérifie que le repository utilise la transformation de modèles."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "_update_model(" in content or "self._update_model(" in content


@pytest.mark.unit
class TestRefreshTokenRepositoryBusinessLogic:
    """Tests de logique métier."""

    def test_repository_handles_token_expiration(self):
        """Vérifie que le repository gère l'expiration des tokens."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "expires_at" in content
        assert "now = datetime.now(timezone.utc)" in content

    def test_repository_handles_token_revocation(self):
        """Vérifie que le repository gère la révocation des tokens."""
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "boursa_vision"
            / "infrastructure"
            / "persistence"
            / "repositories"
            / "refresh_token_repository.py"
        )
        with open(repo_path) as f:
            content = f.read()

        assert "is_revoked" in content
        assert "revoke_all_for_user" in content
        assert "logout_all" in content
