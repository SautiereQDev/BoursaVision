"""
Repository factory for dependency injection.

This module provides a factory pattern for creating repository instances,
enabling easy dependency injection and testability.
"""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession

from application.exceptions import FactoryProviderError

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
from .uow import UnitOfWork


class IRepositoryFactory(Protocol):
    """Interface for repository factory."""

    def create_user_repository(self) -> IUserRepository:
        """Create user repository."""
        ...

    def create_portfolio_repository(self) -> IPortfolioRepository:
        """Create portfolio repository."""
        ...

    def create_market_data_repository(self) -> IMarketDataRepository:
        """Create market data repository."""
        ...

    def create_investment_repository(self) -> IInvestmentRepository:
        """Create investment repository."""
        ...

    def create_unit_of_work(self) -> UnitOfWork:
        """Create unit of work."""
        ...


class SqlAlchemyRepositoryFactory:
    """SQLAlchemy implementation of repository factory."""

    def __init__(self, session: AsyncSession):
        self._session = session

    def create_user_repository(self) -> IUserRepository:
        """Create user repository."""
        return SQLAlchemyUserRepository(self._session)

    def create_portfolio_repository(self) -> IPortfolioRepository:
        """Create portfolio repository."""
        return SQLAlchemyPortfolioRepository(self._session)

    def create_market_data_repository(self) -> IMarketDataRepository:
        """Create market data repository."""
        return SQLAlchemyMarketDataRepository(self._session)

    def create_investment_repository(self) -> IInvestmentRepository:
        """Create investment repository."""
        return SQLAlchemyInvestmentRepository(self._session)

    def create_unit_of_work(self) -> UnitOfWork:
        """Create unit of work."""
        return UnitOfWork(self._session)


class RepositoryFactoryProvider:
    """
    Provider for repository factory instances.

    This class manages the lifecycle of repository factories
    and provides them to application services.
    """

    def __init__(self, session_factory):
        self._session_factory = session_factory

    async def get_factory(self) -> SqlAlchemyRepositoryFactory:
        """Get a repository factory with a new session."""
        session = self._session_factory()
        return SqlAlchemyRepositoryFactory(session)

    async def get_factory_with_session(
        self, session: AsyncSession
    ) -> SqlAlchemyRepositoryFactory:
        """Get a repository factory with an existing session."""
        return SqlAlchemyRepositoryFactory(session)


# Singleton pattern for global repository factory
class RepositoryRegistry:
    """
    Registry for managing repository instances.

    Provides centralized access to repositories and ensures
    consistent configuration across the application.
    """

    def __init__(self):
        self._factories = {}
        self._default_factory_provider = None

    def register_factory_provider(self, provider: RepositoryFactoryProvider) -> None:
        """Register the default factory provider."""
        self._default_factory_provider = provider

    async def get_user_repository(self) -> IUserRepository:
        """Get user repository instance."""
        if self._default_factory_provider is None:
            raise FactoryProviderError()

        factory = await self._default_factory_provider.get_factory()
        return factory.create_user_repository()

    async def get_portfolio_repository(self) -> IPortfolioRepository:
        """Get portfolio repository instance."""
        if self._default_factory_provider is None:
            raise FactoryProviderError()

        factory = await self._default_factory_provider.get_factory()
        return factory.create_portfolio_repository()

    async def get_market_data_repository(self) -> IMarketDataRepository:
        """Get market data repository instance."""
        if self._default_factory_provider is None:
            raise FactoryProviderError()

        factory = await self._default_factory_provider.get_factory()
        return factory.create_market_data_repository()

    async def get_investment_repository(self) -> IInvestmentRepository:
        """Get investment repository instance."""
        if self._default_factory_provider is None:
            raise FactoryProviderError()

        factory = await self._default_factory_provider.get_factory()
        return factory.create_investment_repository()

    async def get_unit_of_work(self) -> UnitOfWork:
        """Get unit of work instance."""
        if self._default_factory_provider is None:
            raise FactoryProviderError()

        factory = await self._default_factory_provider.get_factory()
        return factory.create_unit_of_work()


# Global registry instance
repository_registry = RepositoryRegistry()
