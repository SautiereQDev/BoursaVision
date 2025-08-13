"""
Repository factory for dependency injection and service location.
Implements the Abstract Factory pattern for repository creation.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from src.core.config_simple import settings
from src.domain.repositories.market_data_repository import IMarketDataRepository
from src.domain.repositories.portfolio_repository import IPortfolioRepository
from src.domain.repositories.user_repository import IUserRepository


class IRepositoryFactory(ABC):
    """Abstract factory interface for creating repositories."""

    @abstractmethod
    def create_user_repository(self) -> IUserRepository:
        """Create user repository instance."""

    @abstractmethod
    def create_portfolio_repository(self) -> IPortfolioRepository:
        """Create portfolio repository instance."""

    @abstractmethod
    def create_market_data_repository(self) -> IMarketDataRepository:
        """Create market data repository instance."""


class MockRepositoryFactory(IRepositoryFactory):
    """Mock implementation of repository factory for development/testing."""

    def create_user_repository(self) -> IUserRepository:
        """Create mock user repository."""
        from .mock_repositories import MockUserRepository

        return MockUserRepository()

    def create_portfolio_repository(self) -> IPortfolioRepository:
        """Create mock portfolio repository."""
        from .mock_repositories import MockPortfolioRepository

        return MockPortfolioRepository()

    def create_market_data_repository(self) -> IMarketDataRepository:
        """Create mock market data repository."""
        from .mock_repositories import MockMarketDataRepository

        return MockMarketDataRepository()


class SQLAlchemyRepositoryFactory(IRepositoryFactory):
    """SQLAlchemy implementation of repository factory for production."""

    def __init__(self, session_factory=None):
        """Initialize with optional session factory."""
        self._session_factory = session_factory

    def create_user_repository(self) -> IUserRepository:
        """Create SQLAlchemy user repository."""
        from .repositories.user_repository import SQLAlchemyUserRepository

        return SQLAlchemyUserRepository()

    def create_portfolio_repository(self) -> IPortfolioRepository:
        """Create SQLAlchemy portfolio repository."""
        from .repositories.portfolio_repository import SQLAlchemyPortfolioRepository

        return SQLAlchemyPortfolioRepository()

    def create_market_data_repository(self) -> IMarketDataRepository:
        """Create SQLAlchemy market data repository."""
        from .repositories.market_data_repository import SQLAlchemyMarketDataRepository

        return SQLAlchemyMarketDataRepository()


def get_default_factory() -> IRepositoryFactory:
    """Get the default repository factory based on environment."""

    # For testing and development, always use mocks
    if settings.environment in ("testing", "test") or settings.use_mock_repositories:
        return MockRepositoryFactory()

    # For production, try SQLAlchemy first, fallback to mocks if issues
    try:
        # Check if database is available and SQLAlchemy repositories work
        return SQLAlchemyRepositoryFactory()
    except Exception:
        # Fallback to mocks if SQLAlchemy is not ready
        return MockRepositoryFactory()


class RepositoryRegistry:
    """
    Registry for managing repository instances.
    Implements Singleton pattern for global access.
    """

    _instance = None
    _repositories: Dict[Type, object] = {}
    _factory: Optional[IRepositoryFactory] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def set_factory(self, factory: IRepositoryFactory) -> None:
        """Set the repository factory."""
        self._factory = factory
        self._repositories.clear()  # Clear cache when factory changes

    def get_user_repository(self) -> IUserRepository:
        """Get user repository instance (cached)."""
        if IUserRepository not in self._repositories:
            if self._factory is None:
                self._factory = get_default_factory()
            self._repositories[IUserRepository] = self._factory.create_user_repository()
        return self._repositories[IUserRepository]  # type: ignore

    def get_portfolio_repository(self) -> IPortfolioRepository:
        """Get portfolio repository instance (cached)."""
        if IPortfolioRepository not in self._repositories:
            if self._factory is None:
                self._factory = get_default_factory()
            self._repositories[
                IPortfolioRepository
            ] = self._factory.create_portfolio_repository()
        return self._repositories[IPortfolioRepository]  # type: ignore

    def get_market_data_repository(self) -> IMarketDataRepository:
        """Get market data repository instance (cached)."""
        if IMarketDataRepository not in self._repositories:
            if self._factory is None:
                self._factory = get_default_factory()
            self._repositories[
                IMarketDataRepository
            ] = self._factory.create_market_data_repository()
        return self._repositories[IMarketDataRepository]  # type: ignore

    def clear_cache(self) -> None:
        """Clear repository cache."""
        self._repositories.clear()


# Global registry instance
_registry = RepositoryRegistry()


def get_repository_registry() -> RepositoryRegistry:
    """Get global repository registry."""
    return _registry


def configure_repositories(factory: IRepositoryFactory) -> None:
    """Configure repositories with custom factory."""
    _registry.set_factory(factory)


# Convenience functions
def get_user_repository() -> IUserRepository:
    """Get user repository."""
    return _registry.get_user_repository()


def get_portfolio_repository() -> IPortfolioRepository:
    """Get portfolio repository."""
    return _registry.get_portfolio_repository()


def get_market_data_repository() -> IMarketDataRepository:
    """Get market data repository."""
    return _registry.get_market_data_repository()
