"""
Tests d'intégration pour SQLAlchemyRefreshTokenRepository.

Tests avec exécution réelle du code pour améliorer la couverture,
conformes aux principes de l'Architecture Clean.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

import pytest
from sqlalchemy.engine.result import Result, ScalarResult

from boursa_vision.domain.entities.refresh_token import (
    RefreshToken as DomainRefreshToken,
)
from boursa_vision.infrastructure.persistence.models.refresh_tokens import RefreshToken
from boursa_vision.infrastructure.persistence.repositories.refresh_token_repository import (
    SQLAlchemyRefreshTokenRepository,
)


@pytest.mark.unit
@pytest.mark.asyncio
class TestSQLAlchemyRefreshTokenRepositoryIntegration:
    """Tests d'intégration avec exécution réelle du code."""

    def setup_method(self):
        """Configuration pour chaque test."""
        self.mock_session = AsyncMock()
        self.repository = SQLAlchemyRefreshTokenRepository(self.mock_session)

        self.test_user_id = uuid4()
        self.test_token_id = uuid4()
        self.test_token_string = "test_refresh_token_12345"

        # Dates de test
        self.now = datetime.now(UTC)
        self.expires_at = self.now + timedelta(days=30)
        self.created_at = self.now - timedelta(hours=1)

    def _create_domain_token(self, **overrides) -> DomainRefreshToken:
        """Créer un token de domaine pour les tests."""
        default_data = {
            "id": self.test_token_id,
            "token": self.test_token_string,
            "user_id": self.test_user_id,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "last_used_at": None,
            "is_revoked": False,
            "revoke_reason": "",
            "ip_address": "127.0.0.1",
            "user_agent": "test-agent",
        }
        default_data.update(overrides)
        return DomainRefreshToken(**default_data)

    def _create_model_token(self, **overrides) -> RefreshToken:
        """Créer un modèle de persistance pour les tests."""
        default_data = {
            "id": self.test_token_id,
            "token": self.test_token_string,
            "user_id": self.test_user_id,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "last_used_at": None,
            "is_revoked": False,
            "revoke_reason": None,
            "ip_address": "127.0.0.1",
            "user_agent": "test-agent",
        }
        default_data.update(overrides)
        return RefreshToken(**default_data)

    async def test_find_by_id_found(self):
        """Test find_by_id avec token trouvé."""
        # Arrange
        model = self._create_model_token()

        mock_result = Mock(spec=Result)
        mock_result.scalar_one_or_none.return_value = model
        self.mock_session.execute.return_value = mock_result

        # Act
        result = await self.repository.find_by_id(self.test_token_id)

        # Assert
        assert result is not None
        assert isinstance(result, DomainRefreshToken)
        assert result.id == self.test_token_id
        assert result.token == self.test_token_string
        assert result.user_id == self.test_user_id
        assert result.is_revoked is False
        self.mock_session.execute.assert_called_once()

    async def test_find_by_id_not_found(self):
        """Test find_by_id avec token non trouvé."""
        # Arrange
        mock_result = Mock(spec=Result)
        mock_result.scalar_one_or_none.return_value = None
        self.mock_session.execute.return_value = mock_result

        # Act
        result = await self.repository.find_by_id(self.test_token_id)

        # Assert
        assert result is None
        self.mock_session.execute.assert_called_once()

    async def test_save_create_new_token(self):
        """Test save pour créer un nouveau token."""
        # Arrange
        domain_token = self._create_domain_token()

        # Mock find_by_id pour retourner None (token inexistant)
        mock_find_result = Mock(spec=Result)
        mock_find_result.scalar_one_or_none.return_value = None
        self.mock_session.execute.return_value = mock_find_result

        # Act
        result = await self.repository.save(domain_token)

        # Assert
        assert result is not None
        assert isinstance(result, DomainRefreshToken)
        assert result.token == self.test_token_string
        self.mock_session.add.assert_called_once()
        self.mock_session.flush.assert_called_once()

    async def test_save_update_existing_token(self):
        """Test save pour mettre à jour un token existant."""
        # Arrange
        domain_token = self._create_domain_token(is_revoked=True, revoke_reason="test")
        existing_model = self._create_model_token()

        # Mock find_by_id pour retourner un token existant
        mock_find_result = Mock(spec=Result)
        mock_find_result.scalar_one_or_none.return_value = existing_model

        # Mock update - première execution pour find_by_id, deuxième pour update
        self.mock_session.execute.side_effect = [mock_find_result, mock_find_result]

        # Act
        result = await self.repository.save(domain_token)

        # Assert
        assert result is not None
        assert isinstance(result, DomainRefreshToken)
        assert result.is_revoked is True
        assert result.revoke_reason == "test"
        assert self.mock_session.execute.call_count == 2
        self.mock_session.flush.assert_called_once()

    async def test_update_existing_token(self):
        """Test update avec token existant."""
        # Arrange
        domain_token = self._create_domain_token(last_used_at=self.now)
        model = self._create_model_token()

        mock_result = Mock(spec=Result)
        mock_result.scalar_one_or_none.return_value = model
        self.mock_session.execute.return_value = mock_result

        # Act
        result = await self.repository.update(domain_token)

        # Assert
        assert result is not None
        assert isinstance(result, DomainRefreshToken)
        assert model.last_used_at == self.now
        self.mock_session.flush.assert_called_once()

    async def test_update_nonexistent_token_raises_error(self):
        """Test update avec token inexistant lève une erreur."""
        # Arrange
        domain_token = self._create_domain_token()

        mock_result = Mock(spec=Result)
        mock_result.scalar_one_or_none.return_value = None
        self.mock_session.execute.return_value = mock_result

        # Act & Assert
        with pytest.raises(
            ValueError, match=f"RefreshToken with ID {self.test_token_id} not found"
        ):
            await self.repository.update(domain_token)

    async def test_delete_existing_token(self):
        """Test delete avec token existant."""
        # Arrange
        model = self._create_model_token()

        mock_result = Mock(spec=Result)
        mock_result.scalar_one_or_none.return_value = model
        self.mock_session.execute.return_value = mock_result

        # Act
        result = await self.repository.delete(self.test_token_id)

        # Assert
        assert result is True
        self.mock_session.delete.assert_called_once_with(model)

    async def test_delete_nonexistent_token(self):
        """Test delete avec token inexistant."""
        # Arrange
        mock_result = Mock(spec=Result)
        mock_result.scalar_one_or_none.return_value = None
        self.mock_session.execute.return_value = mock_result

        # Act
        result = await self.repository.delete(self.test_token_id)

        # Assert
        assert result is False
        self.mock_session.delete.assert_not_called()

    async def test_find_by_token_found(self):
        """Test find_by_token avec token trouvé."""
        # Arrange
        model = self._create_model_token()

        mock_result = Mock(spec=Result)
        mock_result.scalar_one_or_none.return_value = model
        self.mock_session.execute.return_value = mock_result

        # Act
        result = await self.repository.find_by_token(self.test_token_string)

        # Assert
        assert result is not None
        assert isinstance(result, DomainRefreshToken)
        assert result.token == self.test_token_string
        self.mock_session.execute.assert_called_once()

    async def test_find_by_token_not_found(self):
        """Test find_by_token avec token non trouvé."""
        # Arrange
        mock_result = Mock(spec=Result)
        mock_result.scalar_one_or_none.return_value = None
        self.mock_session.execute.return_value = mock_result

        # Act
        result = await self.repository.find_by_token("unknown_token")

        # Assert
        assert result is None
        self.mock_session.execute.assert_called_once()

    async def test_find_by_user_id(self):
        """Test find_by_user_id retourne tous les tokens d'un utilisateur."""
        # Arrange
        models = [
            self._create_model_token(id=uuid4(), token="token1"),
            self._create_model_token(id=uuid4(), token="token2"),
        ]

        mock_result = Mock(spec=Result)
        mock_scalars = Mock(spec=ScalarResult)
        mock_scalars.all.return_value = models
        mock_result.scalars.return_value = mock_scalars
        self.mock_session.execute.return_value = mock_result

        # Act
        result = await self.repository.find_by_user_id(self.test_user_id)

        # Assert
        assert len(result) == 2
        assert all(isinstance(token, DomainRefreshToken) for token in result)
        assert all(token.user_id == self.test_user_id for token in result)
        self.mock_session.execute.assert_called_once()

    async def test_find_active_by_user_id(self):
        """Test find_active_by_user_id retourne seulement les tokens actifs."""
        # Arrange - un token actif, les autres ne sont pas inclus dans le mock
        future_date = self.now + timedelta(days=30)

        active_model = self._create_model_token(
            id=uuid4(), token="active_token", expires_at=future_date, is_revoked=False
        )

        # Seulement le token actif devrait être retourné
        models = [active_model]

        mock_result = Mock(spec=Result)
        mock_scalars = Mock(spec=ScalarResult)
        mock_scalars.all.return_value = models
        mock_result.scalars.return_value = mock_scalars
        self.mock_session.execute.return_value = mock_result

        # Act
        result = await self.repository.find_active_by_user_id(self.test_user_id)

        # Assert
        assert len(result) == 1
        assert result[0].token == "active_token"
        assert result[0].is_revoked is False
        self.mock_session.execute.assert_called_once()

    async def test_revoke_all_for_user(self):
        """Test revoke_all_for_user révoque tous les tokens actifs."""
        # Arrange
        models = [
            self._create_model_token(id=uuid4(), token="token1", is_revoked=False),
            self._create_model_token(id=uuid4(), token="token2", is_revoked=False),
        ]

        mock_result = Mock(spec=Result)
        mock_scalars = Mock(spec=ScalarResult)
        mock_scalars.all.return_value = models
        mock_result.scalars.return_value = mock_scalars
        self.mock_session.execute.return_value = mock_result

        # Act
        count = await self.repository.revoke_all_for_user(
            self.test_user_id, "logout_all"
        )

        # Assert
        assert count == 2
        for model in models:
            assert model.is_revoked is True
            assert model.revoke_reason == "logout_all"
        self.mock_session.flush.assert_called_once()

    async def test_cleanup_expired_tokens(self):
        """Test cleanup_expired_tokens supprime les tokens expirés."""
        # Arrange
        cutoff_date = self.now - timedelta(days=1)
        expired_models = [
            self._create_model_token(
                id=uuid4(), expires_at=cutoff_date - timedelta(hours=1)
            ),
            self._create_model_token(
                id=uuid4(), expires_at=cutoff_date - timedelta(hours=2)
            ),
        ]

        mock_result = Mock(spec=Result)
        mock_scalars = Mock(spec=ScalarResult)
        mock_scalars.all.return_value = expired_models
        mock_result.scalars.return_value = mock_scalars
        self.mock_session.execute.return_value = mock_result

        # Act
        count = await self.repository.cleanup_expired_tokens(cutoff_date)

        # Assert
        assert count == 2
        assert self.mock_session.delete.call_count == 2
        self.mock_session.flush.assert_called_once()

    async def test_count_active_sessions(self):
        """Test count_active_sessions compte les sessions actives."""
        # Arrange
        active_models = [
            self._create_model_token(id=uuid4(), token="token1"),
            self._create_model_token(id=uuid4(), token="token2"),
            self._create_model_token(id=uuid4(), token="token3"),
        ]

        mock_result = Mock(spec=Result)
        mock_scalars = Mock(spec=ScalarResult)
        mock_scalars.all.return_value = active_models
        mock_result.scalars.return_value = mock_scalars
        self.mock_session.execute.return_value = mock_result

        # Act
        count = await self.repository.count_active_sessions(self.test_user_id)

        # Assert
        assert count == 3
        self.mock_session.execute.assert_called_once()

    def test_to_domain_conversion(self):
        """Test la conversion du modèle vers l'entité domaine."""
        # Arrange
        model = self._create_model_token(
            revoke_reason="test_reason", last_used_at=self.now
        )

        # Act
        domain_entity = self.repository._to_domain(model)

        # Assert
        assert isinstance(domain_entity, DomainRefreshToken)
        assert domain_entity.id == model.id
        assert domain_entity.token == model.token
        assert domain_entity.user_id == model.user_id
        assert domain_entity.expires_at == model.expires_at
        assert domain_entity.created_at == model.created_at
        assert domain_entity.last_used_at == model.last_used_at
        assert domain_entity.is_revoked == model.is_revoked
        assert domain_entity.revoke_reason == model.revoke_reason
        assert domain_entity.ip_address == model.ip_address
        assert domain_entity.user_agent == model.user_agent

    def test_to_domain_conversion_with_nulls(self):
        """Test la conversion avec des valeurs nulles."""
        # Arrange
        model = self._create_model_token(
            revoke_reason=None, ip_address=None, user_agent=None
        )

        # Act
        domain_entity = self.repository._to_domain(model)

        # Assert
        assert domain_entity.revoke_reason == ""
        assert domain_entity.ip_address == ""
        assert domain_entity.user_agent == ""

    def test_to_persistence_conversion(self):
        """Test la conversion de l'entité domaine vers le modèle."""
        # Arrange
        domain_entity = self._create_domain_token(
            revoke_reason="test_reason", last_used_at=self.now
        )

        # Act
        model = self.repository._to_persistence(domain_entity)

        # Assert
        assert isinstance(model, RefreshToken)
        assert model.id == domain_entity.id
        assert model.token == domain_entity.token
        assert model.user_id == domain_entity.user_id
        assert model.expires_at == domain_entity.expires_at
        assert model.created_at == domain_entity.created_at
        assert model.last_used_at == domain_entity.last_used_at
        assert model.is_revoked == domain_entity.is_revoked
        assert model.revoke_reason == domain_entity.revoke_reason
        assert model.ip_address == domain_entity.ip_address
        assert model.user_agent == domain_entity.user_agent

    def test_to_persistence_conversion_with_empty_strings(self):
        """Test la conversion avec des chaînes vides."""
        # Arrange
        domain_entity = self._create_domain_token(
            revoke_reason="", ip_address="", user_agent=""
        )

        # Act
        model = self.repository._to_persistence(domain_entity)

        # Assert
        assert model.revoke_reason is None
        assert model.ip_address is None
        assert model.user_agent is None

    def test_update_model_method(self):
        """Test la méthode _update_model."""
        # Arrange
        original_model = self._create_model_token()
        updated_entity = self._create_domain_token(
            token="new_token",
            last_used_at=self.now,
            is_revoked=True,
            revoke_reason="updated_reason",
        )

        # Act
        self.repository._update_model(original_model, updated_entity)

        # Assert
        assert original_model.token == "new_token"
        assert original_model.last_used_at == self.now
        assert original_model.is_revoked is True
        assert original_model.revoke_reason == "updated_reason"


@pytest.mark.unit
class TestSQLAlchemyRefreshTokenRepositoryEdgeCases:
    """Tests pour les cas limites et erreurs."""

    def setup_method(self):
        """Configuration pour chaque test."""
        self.mock_session = AsyncMock()
        self.repository = SQLAlchemyRefreshTokenRepository(self.mock_session)

    def test_repository_initialization(self):
        """Test l'initialisation du repository."""
        # Act
        repo = SQLAlchemyRefreshTokenRepository(self.mock_session)

        # Assert
        assert repo.session == self.mock_session

    async def test_empty_list_operations(self):
        """Test les opérations qui retournent des listes vides."""
        # Arrange
        mock_result = Mock(spec=Result)
        mock_scalars = Mock(spec=ScalarResult)
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        self.mock_session.execute.return_value = mock_result

        # Act
        user_tokens = await self.repository.find_by_user_id(uuid4())
        active_tokens = await self.repository.find_active_by_user_id(uuid4())

        # Assert
        assert user_tokens == []
        assert active_tokens == []

    async def test_revoke_all_for_user_no_tokens(self):
        """Test revoke_all_for_user quand il n'y a pas de tokens."""
        # Arrange
        mock_result = Mock(spec=Result)
        mock_scalars = Mock(spec=ScalarResult)
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        self.mock_session.execute.return_value = mock_result

        # Act
        count = await self.repository.revoke_all_for_user(uuid4())

        # Assert
        assert count == 0
        self.mock_session.flush.assert_called_once()

    async def test_cleanup_expired_tokens_no_tokens(self):
        """Test cleanup_expired_tokens quand il n'y a pas de tokens expirés."""
        # Arrange
        mock_result = Mock(spec=Result)
        mock_scalars = Mock(spec=ScalarResult)
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        self.mock_session.execute.return_value = mock_result

        # Act
        count = await self.repository.cleanup_expired_tokens(datetime.now(UTC))

        # Assert
        assert count == 0
        self.mock_session.delete.assert_not_called()
        self.mock_session.flush.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
