"""
Unit of Work pattern implementation for the trading platform.

This module provides transaction management and coordination between
multiple repositories following the Unit of Work pattern.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...domain.repositories.investment_repository import IInvestmentRepository
from ...domain.repositories.market_data_repository import IMarketDataRepository
from ...domain.repositories.portfolio_repository import IPortfolioRepository
from ...domain.repositories.user_repository import IUserRepository
from .repositories import (
    SQLAlchemyInvestmentRepository,
    SQLAlchemyMarketDataRepository,
    SQLAlchemyPortfolioRepository,
    SQLAlchemyUserRepository,
)


class UnitOfWork:
    """
    Unit of Work implementation for coordinating repository operations.

    Provides transaction management and ensures data consistency
    across multiple repository operations.
    """

    def __init__(self, session: AsyncSession):
        self._session = session
        self._repositories: Dict[str, Any] = {}
        self._is_committed = False

    @property
    def users(self) -> IUserRepository:
        """Get user repository."""
        if "users" not in self._repositories:
            self._repositories["users"] = SQLAlchemyUserRepository(self._session)
        return self._repositories["users"]

    @property
    def portfolios(self) -> IPortfolioRepository:
        """Get portfolio repository."""
        if "portfolios" not in self._repositories:
            self._repositories["portfolios"] = SQLAlchemyPortfolioRepository(
                self._session
            )
        return self._repositories["portfolios"]

    @property
    def market_data(self) -> IMarketDataRepository:
        """Get market data repository."""
        if "market_data" not in self._repositories:
            self._repositories["market_data"] = SQLAlchemyMarketDataRepository(
                self._session
            )
        return self._repositories["market_data"]

    @property
    def investments(self) -> IInvestmentRepository:
        """Get investment repository."""
        if "investments" not in self._repositories:
            self._repositories["investments"] = SQLAlchemyInvestmentRepository(
                self._session
            )
        return self._repositories["investments"]

    async def commit(self) -> None:
        """Commit the current transaction."""
        if not self._is_committed:
            await self._session.commit()
            self._is_committed = True

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self._session.rollback()
        self._is_committed = False

    async def flush(self) -> None:
        """Flush pending changes to the database without committing."""
        await self._session.flush()

    async def refresh(self, instance: Any) -> None:
        """Refresh an entity from the database."""
        await self._session.refresh(instance)

    async def close(self) -> None:
        """Close the session."""
        await self._session.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit with automatic rollback on exception."""
        if exc_type is not None:
            await self.rollback()
        elif not self._is_committed:
            await self.commit()
        await self.close()


class UnitOfWorkFactory:
    """Factory for creating Unit of Work instances."""

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def create(self) -> UnitOfWork:
        """Create a new Unit of Work instance."""
        session = self._session_factory()
        return UnitOfWork(session)

    async def create_with_session(self, session: AsyncSession) -> UnitOfWork:
        """Create a Unit of Work with an existing session."""
        return UnitOfWork(session)


class AutoTransaction:
    """
    Context manager for automatic transaction handling.

    Usage:
        async with AutoTransaction(uow) as tx:
            # Perform operations
            await tx.users.save(user)
            await tx.portfolios.save(portfolio)
            # Automatic commit on success, rollback on exception
    """

    def __init__(self, uow: UnitOfWork):
        self._uow = uow

    async def __aenter__(self):
        return self._uow

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self._uow.rollback()
        else:
            await self._uow.commit()
        return False  # Don't suppress exceptions
