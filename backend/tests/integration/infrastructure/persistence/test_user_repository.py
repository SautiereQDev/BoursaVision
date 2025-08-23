"""
Tests unitaires et d'intégration pour la classe SQLAlchemyUserRepository.

Ce module contient les tests pour vérifier le bon fonctionnement
du repository des utilisateurs avec des mocks et quelques tests d'intégration.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from boursa_vision.domain.entities.user import User, UserRole
from boursa_vision.domain.value_objects.money import Currency
from boursa_vision.infrastructure.persistence.repositories.user_repository import (
    SQLAlchemyUserRepository,
)


# Simple User factory for testing
def create_test_user(**kwargs):
    """Create a test user with default values."""
    defaults = {
        "id": uuid4(),
        "username": f"testuser_{uuid4().hex[:8]}",
        "email": f"test_{uuid4().hex[:8]}@example.com",
        "first_name": "Test",
        "last_name": "User",
        "role": UserRole.VIEWER,
        "is_active": True,
        "email_verified": False,
        "preferred_currency": Currency.USD,
        "two_factor_enabled": False,
        "created_at": datetime.now(UTC),
        "last_login": None,
    }
    defaults.update(kwargs)
    return User(**defaults)


@pytest.mark.unit
class TestSQLAlchemyUserRepositoryUnit:
    """Tests unitaires du repository utilisateur avec mocks."""

    def test_repository_initialization(self):
        """Test d'initialisation du repository."""
        repo = SQLAlchemyUserRepository()
        assert repo is not None
        assert hasattr(repo, "_mapper")

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_id_found(self, mock_get_session):
        """Test find_by_id avec utilisateur trouvé."""
        # Arrange
        user_id = uuid4()
        user = create_test_user(id=user_id)

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # Mock DB model
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Mock the mapper to return our domain user
        repo._mapper.to_domain = MagicMock(return_value=user)

        # Act
        result = await repo.find_by_id(user_id)

        # Assert
        assert result == user
        mock_session.execute.assert_called_once()
        repo._mapper.to_domain.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_id_not_found(self, mock_get_session):
        """Test find_by_id avec utilisateur non trouvé."""
        # Arrange
        user_id = uuid4()

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.find_by_id(user_id)

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_email_found(self, mock_get_session):
        """Test find_by_email avec utilisateur trouvé."""
        # Arrange
        email = "test@example.com"
        user = create_test_user(email=email)

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # Mock DB model
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        repo._mapper.to_domain = MagicMock(return_value=user)

        # Act
        result = await repo.find_by_email(email)

        # Assert
        assert result == user
        mock_session.execute.assert_called_once()
        repo._mapper.to_domain.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_email_not_found(self, mock_get_session):
        """Test find_by_email avec utilisateur non trouvé."""
        # Arrange
        email = "nonexistent@example.com"

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.find_by_email(email)

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_username_found(self, mock_get_session):
        """Test find_by_username avec utilisateur trouvé."""
        # Arrange
        username = "testuser"
        user = create_test_user(username=username)

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()  # Mock DB model
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        repo._mapper.to_domain = MagicMock(return_value=user)

        # Act
        result = await repo.find_by_username(username)

        # Assert
        assert result == user
        mock_session.execute.assert_called_once()
        repo._mapper.to_domain.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_username_not_found(self, mock_get_session):
        """Test find_by_username avec utilisateur non trouvé."""
        # Arrange
        username = "nonexistent"

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.find_by_username(username)

        # Assert
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_role_multiple_users(self, mock_get_session):
        """Test find_by_role avec plusieurs utilisateurs."""
        # Arrange
        role = UserRole.ADMIN
        users = [create_test_user(role=role) for _ in range(3)]

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_db_models = [MagicMock() for _ in range(3)]  # Mock DB models
        mock_result.scalars().all.return_value = mock_db_models
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        repo._mapper.to_domain = MagicMock(side_effect=users)

        # Act
        result = await repo.find_by_role(role)

        # Assert
        assert len(result) == 3
        assert result == users
        mock_session.execute.assert_called_once()
        assert repo._mapper.to_domain.call_count == 3

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_role_no_users(self, mock_get_session):
        """Test find_by_role sans utilisateurs."""
        # Arrange
        role = UserRole.TRADER

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalars().all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.find_by_role(role)

        # Assert
        assert result == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_active_users(self, mock_get_session):
        """Test find_active_users."""
        # Arrange
        active_users = [create_test_user(is_active=True) for _ in range(2)]

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_db_models = [MagicMock() for _ in range(2)]
        mock_result.scalars().all.return_value = mock_db_models
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        repo._mapper.to_domain = MagicMock(side_effect=active_users)

        # Act
        result = await repo.find_active_users()

        # Assert
        assert len(result) == 2
        assert result == active_users
        mock_session.execute.assert_called_once()
        assert repo._mapper.to_domain.call_count == 2

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_all_with_pagination(self, mock_get_session):
        """Test find_all avec pagination."""
        # Arrange
        users = [create_test_user() for _ in range(5)]

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_db_models = [MagicMock() for _ in range(5)]
        mock_result.scalars().all.return_value = mock_db_models
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        repo._mapper.to_domain = MagicMock(side_effect=users)

        # Act
        result = await repo.find_all(offset=0, limit=5)

        # Assert
        assert len(result) == 5
        assert result == users
        mock_session.execute.assert_called_once()
        assert repo._mapper.to_domain.call_count == 5

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_exists_by_email_true(self, mock_get_session):
        """Test exists_by_email retourne True."""
        # Arrange
        email = "existing@example.com"

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.exists_by_email(email)

        # Assert
        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_exists_by_email_false(self, mock_get_session):
        """Test exists_by_email retourne False."""
        # Arrange
        email = "nonexistent@example.com"

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.exists_by_email(email)

        # Assert
        assert result is False
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_exists_by_username_true(self, mock_get_session):
        """Test exists_by_username retourne True."""
        # Arrange
        username = "existinguser"

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.exists_by_username(username)

        # Assert
        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_exists_by_username_false(self, mock_get_session):
        """Test exists_by_username retourne False."""
        # Arrange
        username = "nonexistentuser"

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.exists_by_username(username)

        # Assert
        assert result is False
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_count_by_role(self, mock_get_session):
        """Test count_by_role."""
        # Arrange
        role = UserRole.ADMIN
        expected_count = 5

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar.return_value = expected_count
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.count_by_role(role)

        # Assert
        assert result == expected_count
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_save_new_user(self, mock_get_session):
        """Test save avec nouvel utilisateur."""
        # Arrange
        user = create_test_user()

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock that user doesn't exist yet
        mock_session.get.return_value = None

        mock_persistence_model = MagicMock()
        repo = SQLAlchemyUserRepository()
        repo._mapper.to_persistence = MagicMock(return_value=mock_persistence_model)
        repo._mapper.to_domain = MagicMock(return_value=user)

        # Act
        result = await repo.save(user)

        # Assert
        assert result == user
        mock_session.add.assert_called_once_with(mock_persistence_model)
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        repo._mapper.to_persistence.assert_called_once_with(user)
        repo._mapper.to_domain.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_save_existing_user(self, mock_get_session):
        """Test save avec utilisateur existant."""
        # Arrange
        user = create_test_user()

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock that user already exists
        mock_existing_model = MagicMock()
        mock_session.get.return_value = mock_existing_model

        mock_persistence_model = MagicMock()
        repo = SQLAlchemyUserRepository()
        repo._mapper.to_persistence = MagicMock(return_value=mock_persistence_model)
        repo._mapper.to_domain = MagicMock(return_value=user)

        # Act
        result = await repo.save(user)

        # Assert
        assert result == user
        mock_session.add.assert_not_called()  # Should not add existing user
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        repo._mapper.to_persistence.assert_called_once_with(user)
        repo._mapper.to_domain.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_delete_existing_user(self, mock_get_session):
        """Test delete avec utilisateur existant."""
        # Arrange
        user_id = uuid4()

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock execute result with rowcount > 0 (user found and deleted)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.delete(user_id)

        # Assert
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_delete_nonexistent_user(self, mock_get_session):
        """Test delete avec utilisateur inexistant."""
        # Arrange
        user_id = uuid4()

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock execute result with rowcount = 0 (no user found)
        mock_result = MagicMock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.delete(user_id)

        # Assert
        assert result is False
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_update_existing_user(self, mock_get_session):
        """Test update avec utilisateur existant."""
        # Arrange
        user = create_test_user()

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_existing_model = MagicMock()
        mock_existing_model.__table__ = MagicMock()
        mock_existing_model.__table__.columns = [
            MagicMock(name="username"),
            MagicMock(name="email"),
        ]
        mock_session.get.return_value = mock_existing_model

        mock_persistence_model = MagicMock()
        mock_persistence_model.username = "updated_username"
        mock_persistence_model.email = "updated@example.com"

        repo = SQLAlchemyUserRepository()
        repo._mapper.to_persistence = MagicMock(return_value=mock_persistence_model)
        repo._mapper.to_domain = MagicMock(return_value=user)

        # Act
        result = await repo.update(user)

        # Assert
        assert result == user
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        repo._mapper.to_persistence.assert_called_once_with(user)
        repo._mapper.to_domain.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_update_nonexistent_user(self, mock_get_session):
        """Test update avec utilisateur inexistant."""
        # Arrange
        user = create_test_user()

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_session.get.return_value = None

        repo = SQLAlchemyUserRepository()

        # Act & Assert
        with pytest.raises(ValueError, match=f"User with id {user.id} not found"):
            await repo.update(user)

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_email_for_auth(self, mock_get_session):
        """Test find_by_email_for_auth."""
        # Arrange
        email = "auth@example.com"
        user = create_test_user(email=email)

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        repo._mapper.to_domain = MagicMock(return_value=user)

        # Act
        result = await repo.find_by_email_for_auth(email)

        # Assert
        assert result == user
        mock_session.execute.assert_called_once()
        repo._mapper.to_domain.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_username_for_auth(self, mock_get_session):
        """Test find_by_username_for_auth."""
        # Arrange
        username = "authuser"
        user = create_test_user(username=username)

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        repo._mapper.to_domain = MagicMock(return_value=user)

        # Act
        result = await repo.find_by_username_for_auth(username)

        # Assert
        assert result == user
        mock_session.execute.assert_called_once()
        repo._mapper.to_domain.assert_called_once()


@pytest.mark.unit
class TestSQLAlchemyUserRepositoryEdgeCases:
    """Tests des cas limites et de gestion d'erreur."""

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_mapper_error_handling(self, mock_get_session):
        """Test gestion d'erreur du mapper."""
        # Arrange
        user_id = uuid4()

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = MagicMock()
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        repo._mapper.to_domain = MagicMock(side_effect=Exception("Mapping error"))

        # Act & Assert
        with pytest.raises(Exception, match="Mapping error"):
            await repo.find_by_id(user_id)

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_database_session_error(self, mock_get_session):
        """Test gestion d'erreur de session de base de données."""
        # Arrange
        user_id = uuid4()

        mock_get_session.side_effect = Exception("Database connection error")

        repo = SQLAlchemyUserRepository()

        # Act & Assert
        with pytest.raises(Exception, match="Database connection error"):
            await repo.find_by_id(user_id)

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_count_with_none_result(self, mock_get_session):
        """Test count_by_role avec résultat None."""
        # Arrange
        role = UserRole.VIEWER

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.count_by_role(role)

        # Assert
        assert result == 0

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_exists_with_none_result(self, mock_get_session):
        """Test exists_by_email avec résultat None."""
        # Arrange
        email = "test@example.com"

        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()

        # Act
        result = await repo.exists_by_email(email)

        # Assert
        assert result is False

    def test_user_creation_with_all_fields(self):
        """Test création d'utilisateur avec tous les champs."""
        # Arrange & Act
        user = create_test_user(
            username="fulluser",
            email="full@example.com",
            first_name="Full",
            last_name="User",
            role=UserRole.TRADER,
            is_active=True,
            email_verified=True,
            preferred_currency=Currency.EUR,
            two_factor_enabled=True,
        )

        # Assert
        assert user.username == "fulluser"
        assert user.email == "full@example.com"
        assert user.first_name == "Full"
        assert user.last_name == "User"
        assert user.role == UserRole.TRADER
        assert user.is_active is True
        assert user.email_verified is True
        assert user.preferred_currency == Currency.EUR
        assert user.two_factor_enabled is True

    def test_user_creation_with_defaults(self):
        """Test création d'utilisateur avec valeurs par défaut."""
        # Arrange & Act
        user = create_test_user()

        # Assert
        assert user.role == UserRole.VIEWER
        assert user.is_active is True
        assert user.email_verified is False
        assert user.preferred_currency == Currency.USD
        assert user.two_factor_enabled is False
        assert user.last_login is None
        assert isinstance(user.created_at, datetime)

    def test_user_factory_generates_unique_values(self):
        """Test que la factory génère des valeurs uniques."""
        # Arrange & Act
        user1 = create_test_user()
        user2 = create_test_user()

        # Assert
        assert user1.id != user2.id
        assert user1.username != user2.username
        assert user1.email != user2.email
