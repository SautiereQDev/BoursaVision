"""
Tests fonctionnels pour les repositories SQLAlchemy - version simplifiée.
"""

import uuid
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Import direct pour avoir le vrai coverage
from boursa_vision.infrastructure.persistence.repositories import (
    SQLAlchemyInvestmentRepository,
    SQLAlchemyUserRepository,
)


class TestSQLAlchemyUserRepositoryFunctional:
    """Tests fonctionnels pour SQLAlchemyUserRepository."""

    def test_repository_initialization(self):
        """Test l'initialisation du repository."""
        repo = SQLAlchemyUserRepository()
        assert hasattr(repo, "_mapper")

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_id_not_found(self, mock_get_session):
        """Test find_by_id quand utilisateur non trouvé."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat vide
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        result = await repo.find_by_id(uuid.uuid4())

        # Vérifications
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_email_not_found(self, mock_get_session):
        """Test find_by_email quand utilisateur non trouvé."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat vide
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        result = await repo.find_by_email("notfound@example.com")

        # Vérifications
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_by_username_not_found(self, mock_get_session):
        """Test find_by_username quand utilisateur non trouvé."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat vide
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        result = await repo.find_by_username("notfound")

        # Vérifications
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_exists_by_email_false(self, mock_get_session):
        """Test exists_by_email retourne False."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat
        mock_result = Mock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        result = await repo.exists_by_email("notfound@example.com")

        # Vérifications
        assert result is False
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_exists_by_email_true(self, mock_get_session):
        """Test exists_by_email retourne True."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        result = await repo.exists_by_email("found@example.com")

        # Vérifications
        assert result is True
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_exists_by_username_false(self, mock_get_session):
        """Test exists_by_username retourne False."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat
        mock_result = Mock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        result = await repo.exists_by_username("notfound")

        # Vérifications
        assert result is False
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_count_active_users(self, mock_get_session):
        """Test comptage des utilisateurs actifs."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat
        mock_result = Mock()
        mock_result.scalar.return_value = 5
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        result = await repo.count_active()

        # Vérifications
        assert result == 5
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_find_all_active_empty(self, mock_get_session):
        """Test récupération de tous les utilisateurs actifs (liste vide)."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat vide
        mock_result = Mock()
        mock_result.scalars().all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        result = await repo.find_all_active()

        # Vérifications
        assert result == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_delete_user_not_found(self, mock_get_session):
        """Test suppression d'utilisateur non trouvé."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat de suppression (aucune ligne affectée)
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        user_id = uuid.uuid4()
        result = await repo.delete(user_id)

        # Vérifications
        assert result is False
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.user_repository.get_db_session"
    )
    async def test_delete_user_success(self, mock_get_session):
        """Test suppression d'utilisateur avec succès."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat de suppression
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyUserRepository()
        user_id = uuid.uuid4()
        result = await repo.delete(user_id)

        # Vérifications
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()


class TestSQLAlchemyInvestmentRepositoryFunctional:
    """Tests fonctionnels pour SQLAlchemyInvestmentRepository."""

    def test_repository_initialization(self):
        """Test l'initialisation du repository."""
        repo = SQLAlchemyInvestmentRepository()
        assert hasattr(repo, "_mapper")

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.investment_repository.get_db_session"
    )
    async def test_find_by_id_not_found(self, mock_get_session):
        """Test find_by_id quand investissement non trouvé."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat vide
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyInvestmentRepository()
        result = await repo.find_by_id(uuid.uuid4())

        # Vérifications
        assert result is None
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.investment_repository.get_db_session"
    )
    async def test_find_by_portfolio_id_empty(self, mock_get_session):
        """Test find_by_portfolio_id avec résultat vide."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat vide
        mock_result = Mock()
        mock_result.scalars().all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyInvestmentRepository()
        portfolio_id = uuid.uuid4()
        result = await repo.find_by_portfolio_id(portfolio_id)

        # Vérifications
        assert result == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.investment_repository.get_db_session"
    )
    async def test_delete_investment_success(self, mock_get_session):
        """Test suppression d'investissement avec succès."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat de suppression
        mock_result = Mock()
        mock_result.rowcount = 1
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyInvestmentRepository()
        investment_id = uuid.uuid4()
        result = await repo.delete(investment_id)

        # Vérifications
        assert result is True
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.investment_repository.get_db_session"
    )
    async def test_delete_investment_not_found(self, mock_get_session):
        """Test suppression d'investissement non trouvé."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat de suppression (aucune ligne affectée)
        mock_result = Mock()
        mock_result.rowcount = 0
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyInvestmentRepository()
        investment_id = uuid.uuid4()
        result = await repo.delete(investment_id)

        # Vérifications
        assert result is False
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.investment_repository.get_db_session"
    )
    async def test_find_all_empty(self, mock_get_session):
        """Test find_all avec résultat vide."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat vide
        mock_result = Mock()
        mock_result.scalars().all.return_value = []
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyInvestmentRepository()
        result = await repo.find_all()

        # Vérifications
        assert result == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.investment_repository.get_db_session"
    )
    async def test_exists_false(self, mock_get_session):
        """Test exists retourne False."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat
        mock_result = Mock()
        mock_result.scalar.return_value = 0
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyInvestmentRepository()
        result = await repo.exists(uuid.uuid4())

        # Vérifications
        assert result is False
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.infrastructure.persistence.repositories.investment_repository.get_db_session"
    )
    async def test_exists_true(self, mock_get_session):
        """Test exists retourne True."""
        # Mock de la session
        mock_session = AsyncMock()
        mock_get_session.return_value.__aenter__.return_value = mock_session

        # Mock du résultat
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        repo = SQLAlchemyInvestmentRepository()
        result = await repo.exists(uuid.uuid4())

        # Vérifications
        assert result is True
        mock_session.execute.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
