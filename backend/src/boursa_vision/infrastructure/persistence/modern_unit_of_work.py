"""
Modern Unit of Work Implementation using Python 3.13
==================================================

Combines the Factory pattern with Unit of Work for consistent
transaction management and repository creation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar

from boursa_vision.infrastructure.persistence.factory.repository_factory import (
    AbstractRepositoryFactory,
    RepositoryMode,
    create_repository_factory,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from boursa_vision.domain.repositories.portfolio_repository import IPortfolioRepository
    from boursa_vision.domain.repositories.user_repository import IUserRepository


# Python 3.13 type alias using new 'type' keyword
type SessionType = AsyncSession | None


class ModernUnitOfWork:
    """
    Modern Unit of Work implementation with factory integration
    Uses Python 3.13 slots for optimal performance
    """
    __slots__ = (
        '_factory',
        '_portfolio_repository',
        '_session',
        '_user_repository',
    )

    # Class variable for default factory mode
    default_mode: ClassVar[RepositoryMode] = RepositoryMode.PRODUCTION

    def __init__(self, session: SessionType = None, factory: AbstractRepositoryFactory | None = None):
        """Initialize UoW with optional session and factory"""
        self._session = session
        self._factory = factory or create_repository_factory(self.default_mode)
        self._user_repository: IUserRepository | None = None
        self._portfolio_repository: IPortfolioRepository | None = None

    @property
    def users(self) -> IUserRepository:
        """Lazy-loaded user repository with session injection"""
        if self._user_repository is None:
            self._user_repository = self._factory.create_user_repository(self._session)
        return self._user_repository

    @property
    def portfolios(self) -> IPortfolioRepository:
        """Lazy-loaded portfolio repository with session injection"""
        if self._portfolio_repository is None:
            self._portfolio_repository = self._factory.create_portfolio_repository(self._session)
        return self._portfolio_repository

    async def __aenter__(self) -> ModernUnitOfWork:
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type: type[Exception] | None, exc_val: Exception | None, exc_tb: Any) -> None:
        """Async context manager exit with pattern matching for error handling"""
        if self._session is None:
            return

        match exc_type:
            case None:
                # No exception - commit transaction
                try:
                    await self._session.commit()
                except Exception:
                    await self._session.rollback()
                    raise
            case _:
                # Exception occurred - rollback
                await self._session.rollback()

    async def commit(self) -> None:
        """Explicit commit for manual transaction control"""
        if self._session:
            await self._session.commit()

    async def rollback(self) -> None:
        """Explicit rollback for manual transaction control"""
        if self._session:
            await self._session.rollback()

    def reset_repositories(self) -> None:
        """Reset cached repositories - useful for testing"""
        self._user_repository = None
        self._portfolio_repository = None

    @classmethod
    def create_for_testing(cls, session: SessionType) -> ModernUnitOfWork:
        """Factory method for creating test-optimized UoW instances"""
        test_factory = create_repository_factory(RepositoryMode.TEST)
        return cls(session=session, factory=test_factory)

    @classmethod
    def create_production(cls) -> ModernUnitOfWork:
        """Factory method for creating production UoW instances"""
        production_factory = create_repository_factory(RepositoryMode.PRODUCTION)
        return cls(factory=production_factory)


# Modern dependency injection helper for FastAPI
class UnitOfWorkProvider:
    """
    Provider for UoW instances with Python 3.13 pattern matching
    for dependency resolution
    """

    @staticmethod
    def get_uow_for_context(context: str = "default") -> ModernUnitOfWork:
        """
        Get UoW instance based on context using pattern matching
        Demonstrates Python 3.13 enhanced pattern matching
        """
        match context:
            case "test" | "testing":
                # For testing, require explicit session injection
                raise ValueError("Test context requires explicit session injection")
            case "production" | "prod":
                return ModernUnitOfWork.create_production()
            case "default" | _:
                return ModernUnitOfWork.create_production()


# Usage examples with Python 3.13 features
def example_production_usage():
    """Example of production UoW usage with modern patterns"""

    # Direct instantiation
    uow = ModernUnitOfWork.create_production()

    # Access repositories (lazy-loaded)
    _ = uow.users
    _ = uow.portfolios

    # Pattern matching for context-based creation
    context = "production"
    match context:
        case "test":
            # Would require session injection
            pass
        case "production":
            prod_uow = UnitOfWorkProvider.get_uow_for_context("production")
            _ = prod_uow.users


async def example_transaction_usage():
    """Example of transaction management with async context"""
    from unittest.mock import AsyncMock

    # Mock session for demonstration
    mock_session = AsyncMock()
    
    # Using async context manager
    async with ModernUnitOfWork.create_for_testing(mock_session) as uow:
        # Operations would be performed here
        user_repo = uow.users
        portfolio_repo = uow.portfolios
        
        # Demonstrate repository access
        _ = user_repo
        _ = portfolio_repo
        
        # Transaction automatically handled by __aexit__
        pass


# Modern configuration helper
class UoWConfiguration:
    """Configuration helper for UoW with Python 3.13 dataclass features"""
    
    @staticmethod
    def configure_default_mode(mode: RepositoryMode) -> None:
        """Configure the default repository mode globally"""
        ModernUnitOfWork.default_mode = mode
    
    @staticmethod
    def get_configured_uow(**kwargs) -> ModernUnitOfWork:
        """Get UoW with current configuration"""
        return ModernUnitOfWork(**kwargs)
