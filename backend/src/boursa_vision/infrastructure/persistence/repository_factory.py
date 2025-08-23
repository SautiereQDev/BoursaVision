"""
Repository factory for dependency injection and service location.
Implements the Abstract Factory pattern for repository creation.
"""

from abc import ABC, abstractmethod
from typing import ClassVar

from boursa_vision.domain.repositories.market_data_repository import (
    IMarketDataRepository,
)
from boursa_vision.domain.repositories.portfolio_repository import IPortfolioRepository
from boursa_vision.domain.repositories.user_repository import IUserRepository


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


class SQLAlchemyRepositoryFactory(IRepositoryFactory):
    """SQLAlchemy implementation of repository factory."""

    def create_user_repository(self) -> IUserRepository:
        """Create SQLAlchemy user repository."""
        from boursa_vision.infrastructure.persistence.repositories.user_repository import (
            SQLAlchemyUserRepository,
        )

        return SQLAlchemyUserRepository()

    def create_portfolio_repository(self) -> IPortfolioRepository:
        """Create SQLAlchemy portfolio repository."""
        from boursa_vision.infrastructure.persistence.repositories.portfolio_repository import (
            SQLAlchemyPortfolioRepository,
        )

        return SQLAlchemyPortfolioRepository()

    def create_market_data_repository(self) -> IMarketDataRepository:
        """Create SQLAlchemy market data repository."""
        from boursa_vision.infrastructure.persistence.repositories.market_data_repository import (
            SQLAlchemyMarketDataRepository,
        )

        return SQLAlchemyMarketDataRepository()


class MockRepositoryFactory(IRepositoryFactory):
    """Mock implementation of repository factory for testing."""

    def create_user_repository(self) -> IUserRepository:
        """Create mock user repository."""
        from boursa_vision.infrastructure.persistence.mock_repositories import (
            MockUserRepository,
        )

        return MockUserRepository()

    def create_portfolio_repository(self) -> IPortfolioRepository:
        """Create mock portfolio repository."""
        from boursa_vision.infrastructure.persistence.mock_repositories import (
            MockPortfolioRepository,
        )

        return MockPortfolioRepository()

    def create_market_data_repository(self) -> IMarketDataRepository:
        """Create mock market data repository."""
        from boursa_vision.infrastructure.persistence.mock_repositories import (
            MockMarketDataRepository,
        )

        return MockMarketDataRepository()


class RepositoryRegistry:
    """
    Registry for managing repository instances.
    Implements Singleton pattern for global access.
    """

    _instance = None
    _repositories: ClassVar[dict[type, object]] = {}
    _factory: IRepositoryFactory | None = None

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
                self._factory = SQLAlchemyRepositoryFactory()
            self._repositories[IUserRepository] = self._factory.create_user_repository()
        return self._repositories[IUserRepository]  # type: ignore

    def get_portfolio_repository(self) -> IPortfolioRepository:
        """Get portfolio repository instance (cached)."""
        if IPortfolioRepository not in self._repositories:
            if self._factory is None:
                self._factory = SQLAlchemyRepositoryFactory()
            self._repositories[IPortfolioRepository] = (
                self._factory.create_portfolio_repository()
            )
        return self._repositories[IPortfolioRepository]  # type: ignore

    def get_market_data_repository(self) -> IMarketDataRepository:
        """Get market data repository instance (cached)."""
        if IMarketDataRepository not in self._repositories:
            if self._factory is None:
                self._factory = SQLAlchemyRepositoryFactory()
            self._repositories[IMarketDataRepository] = (
                self._factory.create_market_data_repository()
            )
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
