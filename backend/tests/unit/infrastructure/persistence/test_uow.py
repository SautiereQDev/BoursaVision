"""
Tests for uow.py
Unit of Work pattern implementation tests
"""

import asyncio
import sys
from unittest.mock import AsyncMock, Mock, patch

import pytest

# Mock the problematic imports to avoid dependency issues
sys.modules["sqlalchemy"] = Mock()
sys.modules["sqlalchemy.ext"] = Mock()
sys.modules["sqlalchemy.ext.asyncio"] = Mock()

from boursa_vision.infrastructure.persistence.uow import (
    AutoTransaction,
    UnitOfWork,
    UnitOfWorkFactory,
)


class TestUnitOfWork:
    """Tests for UnitOfWork class"""

    @pytest.fixture
    def mock_session(self):
        """Mock AsyncSession"""
        session = AsyncMock()
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.flush = AsyncMock()
        session.refresh = AsyncMock()
        session.close = AsyncMock()
        return session

    @pytest.fixture
    def unit_of_work(self, mock_session):
        """UnitOfWork instance with mocked session"""
        return UnitOfWork(mock_session)

    @pytest.mark.unit
    def test_unit_of_work_init(self, mock_session):
        """Test UnitOfWork initialization"""
        uow = UnitOfWork(mock_session)

        assert uow._session == mock_session
        assert uow._repositories == {}
        assert uow._is_committed is False

    @pytest.mark.unit
    def test_users_repository_property(self, unit_of_work):
        """Test users repository property lazy loading"""
        with patch(
            "boursa_vision.infrastructure.persistence.uow.SQLAlchemyUserRepository"
        ) as mock_repo:
            # First access creates repository
            repo1 = unit_of_work.users
            mock_repo.assert_called_once_with(unit_of_work._session)

            # Second access returns cached repository
            repo2 = unit_of_work.users
            assert repo1 == repo2
            mock_repo.assert_called_once()  # Still only called once

    @pytest.mark.unit
    def test_portfolios_repository_property(self, unit_of_work):
        """Test portfolios repository property lazy loading"""
        with patch(
            "boursa_vision.infrastructure.persistence.uow.SQLAlchemyPortfolioRepository"
        ) as mock_repo:
            # First access creates repository
            repo1 = unit_of_work.portfolios
            mock_repo.assert_called_once_with(unit_of_work._session)

            # Second access returns cached repository
            repo2 = unit_of_work.portfolios
            assert repo1 == repo2
            mock_repo.assert_called_once()

    @pytest.mark.unit
    def test_market_data_repository_property(self, unit_of_work):
        """Test market_data repository property lazy loading"""
        with patch(
            "boursa_vision.infrastructure.persistence.uow.SQLAlchemyMarketDataRepository"
        ) as mock_repo:
            # First access creates repository
            repo1 = unit_of_work.market_data
            mock_repo.assert_called_once_with(unit_of_work._session)

            # Second access returns cached repository
            repo2 = unit_of_work.market_data
            assert repo1 == repo2
            mock_repo.assert_called_once()

    @pytest.mark.unit
    def test_investments_repository_property(self, unit_of_work):
        """Test investments repository property lazy loading"""
        with patch(
            "boursa_vision.infrastructure.persistence.uow.SQLAlchemyInvestmentRepository"
        ) as mock_repo:
            # First access creates repository
            repo1 = unit_of_work.investments
            mock_repo.assert_called_once_with(unit_of_work._session)

            # Second access returns cached repository
            repo2 = unit_of_work.investments
            assert repo1 == repo2
            mock_repo.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_commit(self, unit_of_work, mock_session):
        """Test commit operation"""
        await unit_of_work.commit()

        mock_session.commit.assert_called_once()
        assert unit_of_work._is_committed is True

    @pytest.mark.unit
    async def test_commit_already_committed(self, unit_of_work, mock_session):
        """Test commit when already committed"""
        unit_of_work._is_committed = True

        await unit_of_work.commit()

        mock_session.commit.assert_not_called()

    @pytest.mark.unit
    async def test_rollback(self, unit_of_work, mock_session):
        """Test rollback operation"""
        unit_of_work._is_committed = True

        await unit_of_work.rollback()

        mock_session.rollback.assert_called_once()
        assert unit_of_work._is_committed is False

    @pytest.mark.unit
    async def test_flush(self, unit_of_work, mock_session):
        """Test flush operation"""
        await unit_of_work.flush()

        mock_session.flush.assert_called_once()

    @pytest.mark.unit
    async def test_refresh(self, unit_of_work, mock_session):
        """Test refresh operation"""
        mock_instance = Mock()

        await unit_of_work.refresh(mock_instance)

        mock_session.refresh.assert_called_once_with(mock_instance)

    @pytest.mark.unit
    async def test_close(self, unit_of_work, mock_session):
        """Test close operation"""
        await unit_of_work.close()

        mock_session.close.assert_called_once()

    @pytest.mark.unit
    async def test_async_context_manager_success(self, unit_of_work, mock_session):
        """Test async context manager with successful execution"""
        async with unit_of_work as uow:
            assert uow == unit_of_work

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

    @pytest.mark.unit
    async def test_async_context_manager_exception(self, unit_of_work, mock_session):
        """Test async context manager with exception"""
        try:
            async with unit_of_work:
                raise ValueError("Test exception")
        except ValueError:
            pass

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()

    @pytest.mark.unit
    async def test_async_context_manager_already_committed(
        self, unit_of_work, mock_session
    ):
        """Test async context manager when already committed"""
        unit_of_work._is_committed = True

        async with unit_of_work:
            # Context manager should not change committed state
            assert unit_of_work._is_committed is True

        mock_session.commit.assert_not_called()
        mock_session.close.assert_called_once()

    @pytest.mark.unit
    def test_repository_caching(self, unit_of_work):
        """Test that repositories are properly cached"""
        with patch(
            "boursa_vision.infrastructure.persistence.uow.SQLAlchemyUserRepository"
        ) as mock_user_repo, patch(
            "boursa_vision.infrastructure.persistence.uow.SQLAlchemyPortfolioRepository"
        ) as mock_portfolio_repo:
            # Access multiple repositories
            users1 = unit_of_work.users
            portfolios1 = unit_of_work.portfolios
            users2 = unit_of_work.users
            portfolios2 = unit_of_work.portfolios

            # Each repository should be created only once
            mock_user_repo.assert_called_once()
            mock_portfolio_repo.assert_called_once()

            # Same instances should be returned
            assert users1 == users2
            assert portfolios1 == portfolios2


class TestUnitOfWorkFactory:
    """Tests for UnitOfWorkFactory class"""

    @pytest.fixture
    def mock_session_factory(self):
        """Mock session factory"""
        factory = Mock()
        factory.return_value = AsyncMock()
        return factory

    @pytest.fixture
    def uow_factory(self, mock_session_factory):
        """UnitOfWorkFactory instance"""
        return UnitOfWorkFactory(mock_session_factory)

    @pytest.mark.unit
    def test_factory_init(self, mock_session_factory):
        """Test UnitOfWorkFactory initialization"""
        factory = UnitOfWorkFactory(mock_session_factory)

        assert factory._session_factory == mock_session_factory

    @pytest.mark.unit
    async def test_create(self, uow_factory, mock_session_factory):
        """Test creating UnitOfWork instance"""
        uow = await uow_factory.create()

        mock_session_factory.assert_called_once()
        assert isinstance(uow, UnitOfWork)
        assert uow._session == mock_session_factory.return_value

    @pytest.mark.unit
    async def test_create_with_session(self, uow_factory):
        """Test creating UnitOfWork with existing session"""
        mock_session = AsyncMock()

        uow = await uow_factory.create_with_session(mock_session)

        assert isinstance(uow, UnitOfWork)
        assert uow._session == mock_session

    @pytest.mark.unit
    async def test_create_multiple_instances(self, uow_factory, mock_session_factory):
        """Test creating multiple UnitOfWork instances"""
        uow1 = await uow_factory.create()
        uow2 = await uow_factory.create()

        assert mock_session_factory.call_count == 2
        assert uow1 != uow2
        assert isinstance(uow1, UnitOfWork)
        assert isinstance(uow2, UnitOfWork)


class TestAutoTransaction:
    """Tests for AutoTransaction class"""

    @pytest.fixture
    def mock_uow(self):
        """Mock UnitOfWork"""
        uow = Mock()
        uow.commit = AsyncMock()
        uow.rollback = AsyncMock()
        return uow

    @pytest.fixture
    def auto_transaction(self, mock_uow):
        """AutoTransaction instance"""
        return AutoTransaction(mock_uow)

    @pytest.mark.unit
    def test_auto_transaction_init(self, mock_uow):
        """Test AutoTransaction initialization"""
        tx = AutoTransaction(mock_uow)

        assert tx._uow == mock_uow

    @pytest.mark.unit
    async def test_auto_transaction_success(self, auto_transaction, mock_uow):
        """Test AutoTransaction with successful execution"""
        async with auto_transaction as tx:
            assert tx == mock_uow

        mock_uow.commit.assert_called_once()
        mock_uow.rollback.assert_not_called()

    @pytest.mark.unit
    async def test_auto_transaction_exception(self, auto_transaction, mock_uow):
        """Test AutoTransaction with exception"""
        with pytest.raises(ValueError):
            async with auto_transaction:
                raise ValueError("Test exception")

        mock_uow.rollback.assert_called_once()
        mock_uow.commit.assert_not_called()

    @pytest.mark.unit
    async def test_auto_transaction_exception_not_suppressed(
        self, auto_transaction, mock_uow
    ):
        """Test that AutoTransaction doesn't suppress exceptions"""
        exception_caught = False

        try:
            async with auto_transaction:
                raise RuntimeError("Custom error")
        except RuntimeError as e:
            exception_caught = True
            assert str(e) == "Custom error"

        assert exception_caught
        mock_uow.rollback.assert_called_once()

    @pytest.mark.unit
    async def test_auto_transaction_nested_operations(self, auto_transaction, mock_uow):
        """Test AutoTransaction with multiple operations"""
        mock_uow.users = Mock()
        mock_uow.portfolios = Mock()
        mock_uow.users.save = AsyncMock()
        mock_uow.portfolios.save = AsyncMock()

        async with auto_transaction as tx:
            await tx.users.save(Mock())
            await tx.portfolios.save(Mock())

        mock_uow.users.save.assert_called_once()
        mock_uow.portfolios.save.assert_called_once()
        mock_uow.commit.assert_called_once()


class TestUnitOfWorkIntegration:
    """Integration tests for UoW components"""

    @pytest.mark.unit
    async def test_complete_workflow(self):
        """Test complete UoW workflow"""
        # Create mock session factory
        mock_session = AsyncMock()
        mock_session_factory = Mock(return_value=mock_session)

        # Create factory and UoW
        factory = UnitOfWorkFactory(mock_session_factory)
        uow = await factory.create()

        # Test repository access and caching
        with patch(
            "boursa_vision.infrastructure.persistence.uow.SQLAlchemyUserRepository"
        ) as mock_repo:
            repo1 = uow.users
            repo2 = uow.users
            assert repo1 == repo2
            mock_repo.assert_called_once()

        # Test transaction operations
        await uow.flush()
        await uow.commit()
        assert uow._is_committed is True

        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    async def test_factory_with_auto_transaction(self):
        """Test UnitOfWorkFactory with AutoTransaction"""
        mock_session = AsyncMock()
        mock_session_factory = Mock(return_value=mock_session)

        factory = UnitOfWorkFactory(mock_session_factory)
        uow = await factory.create()

        async with AutoTransaction(uow) as tx:
            # Simulate some work
            await tx.flush()

        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.unit
    async def test_uow_context_manager_with_repositories(self):
        """Test UoW context manager with repository operations"""
        mock_session = AsyncMock()
        uow = UnitOfWork(mock_session)

        with patch(
            "boursa_vision.infrastructure.persistence.uow.SQLAlchemyUserRepository"
        ) as mock_user_repo:
            async with uow as tx:
                # Access repository during transaction
                tx.users
                mock_user_repo.assert_called_once_with(mock_session)

        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()

    @pytest.mark.unit
    async def test_error_handling_in_transaction_chain(self):
        """Test error handling across transaction operations"""
        mock_session = AsyncMock()

        # Make commit raise an exception
        mock_session.commit.side_effect = Exception("Commit failed")

        uow = UnitOfWork(mock_session)

        with pytest.raises(Exception, match="Commit failed"):
            await uow.commit()

        # Should still be able to rollback
        await uow.rollback()
        mock_session.rollback.assert_called_once()

    @pytest.mark.unit
    async def test_repository_isolation(self):
        """Test that different UoW instances have isolated repositories"""
        mock_session1 = AsyncMock()
        mock_session2 = AsyncMock()

        uow1 = UnitOfWork(mock_session1)
        uow2 = UnitOfWork(mock_session2)

        with patch(
            "boursa_vision.infrastructure.persistence.uow.SQLAlchemyUserRepository"
        ) as mock_repo:
            uow1.users
            uow2.users

            # Should create separate repository instances
            assert mock_repo.call_count == 2
            mock_repo.assert_any_call(mock_session1)
            mock_repo.assert_any_call(mock_session2)

    @pytest.mark.unit
    async def test_session_lifecycle_management(self):
        """Test session lifecycle management"""
        mock_session = AsyncMock()
        uow = UnitOfWork(mock_session)

        # Test refresh operation
        mock_entity = Mock()
        await uow.refresh(mock_entity)
        mock_session.refresh.assert_called_once_with(mock_entity)

        # Test close operation
        await uow.close()
        mock_session.close.assert_called_once()

        # Test multiple operations
        await uow.flush()
        await uow.rollback()

        mock_session.flush.assert_called_once()
        mock_session.rollback.assert_called_once()
