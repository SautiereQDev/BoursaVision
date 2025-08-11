"""
Unit of Work pattern implementation for managing database transactions.
Ensures consistency across multiple repository operations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repositories.market_data_repository import IMarketDataRepository
from src.domain.repositories.portfolio_repository import IPortfolioRepository
from src.domain.repositories.user_repository import IUserRepository
from src.infrastructure.persistence.repositories.market_data_repository import (
    SQLAlchemyMarketDataRepository,
)
from src.infrastructure.persistence.repositories.portfolio_repository import (
    SQLAlchemyPortfolioRepository,
)
from src.infrastructure.persistence.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from src.infrastructure.persistence.sqlalchemy.database import get_db_manager


class IUnitOfWork(ABC):
    """Unit of Work interface."""

    users: IUserRepository
    portfolios: IPortfolioRepository
    market_data: IMarketDataRepository

    @abstractmethod
    async def __aenter__(self):
        """Enter async context."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        pass

    @abstractmethod
    async def commit(self) -> None:
        """Commit the transaction."""
        pass

    @abstractmethod
    async def rollback(self) -> None:
        """Rollback the transaction."""
        pass


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """
    SQLAlchemy implementation of Unit of Work pattern.
    Manages database transactions across multiple repositories.
    """

    def __init__(self):
        self._session: Optional[AsyncSession] = None
        self._db_manager = get_db_manager()

        # Initialize repositories (will be bound to session on enter)
        self.users: IUserRepository = SQLAlchemyUserRepository()
        self.portfolios: IPortfolioRepository = SQLAlchemyPortfolioRepository()
        self.market_data: IMarketDataRepository = SQLAlchemyMarketDataRepository()

    async def __aenter__(self):
        """Enter async context and start transaction."""
        self._session = self._db_manager.session_factory()
        await self._session.__aenter__()

        # Bind repositories to the current session
        self._bind_repositories_to_session()

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and handle transaction."""
        if exc_type is not None:
            await self.rollback()
        else:
            await self.commit()

        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None

    async def commit(self) -> None:
        """Commit the transaction."""
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        """Rollback the transaction."""
        if self._session:
            await self._session.rollback()

    def _bind_repositories_to_session(self) -> None:
        """Bind all repositories to the current session."""
        # This is a simplified approach - in a real implementation,
        # you might want to create new repository instances bound to the session
        if hasattr(self.users, "_session"):
            self.users._session = self._session
        if hasattr(self.portfolios, "_session"):
            self.portfolios._session = self._session
        if hasattr(self.market_data, "_session"):
            self.market_data._session = self._session


class UnitOfWorkFactory:
    """Factory for creating Unit of Work instances."""

    @staticmethod
    def create() -> IUnitOfWork:
        """Create a new Unit of Work instance."""
        return SQLAlchemyUnitOfWork()


# Dependency injection support
_uow_factory: Optional[UnitOfWorkFactory] = None


def init_uow_factory(factory: UnitOfWorkFactory) -> None:
    """Initialize the global Unit of Work factory."""
    # Use module-level assignment instead of global
    # pylint: disable=global-statement
    global _uow_factory
    _uow_factory = factory


def get_uow() -> IUnitOfWork:
    """Get a new Unit of Work instance."""
    if _uow_factory is None:
        # Default factory
        return SQLAlchemyUnitOfWork()
    return _uow_factory.create()
