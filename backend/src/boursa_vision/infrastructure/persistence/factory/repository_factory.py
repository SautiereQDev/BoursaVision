"""
Modern Repository Factory using Python 3.13
============================================

Eliminates duplication between Simple* and standard mappers/repositories
using the Factory pattern with Python 3.13 features.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import TYPE_CHECKING, Protocol, TypeVar

from boursa_vision.domain.repositories.portfolio_repository import IPortfolioRepository
from boursa_vision.domain.repositories.user_repository import IUserRepository

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


# Python 3.13 enhanced enums with auto()
class RepositoryMode(Enum):
    """Repository implementation modes"""
    PRODUCTION = auto()
    TEST = auto()
    SIMPLE = auto()  # For backwards compatibility


# Generic type for repositories
TRepository = TypeVar('TRepository')


class RepositoryFactory(Protocol):
    """Protocol defining repository factory interface"""
    
    def create_user_repository(self, session: AsyncSession | None = None) -> IUserRepository:
        """Create user repository instance"""
        ...
    
    def create_portfolio_repository(self, session: AsyncSession | None = None) -> IPortfolioRepository:
        """Create portfolio repository instance"""
        ...


class AbstractRepositoryFactory(ABC):
    """Abstract base factory for repository creation"""
    
    def __init__(self, mode: RepositoryMode = RepositoryMode.PRODUCTION):
        self.mode = mode
    
    @abstractmethod
    def create_user_repository(self, session: AsyncSession | None = None) -> IUserRepository:
        """Create user repository with appropriate implementation"""
        pass
    
    @abstractmethod  
    def create_portfolio_repository(self, session: AsyncSession | None = None) -> IPortfolioRepository:
        """Create portfolio repository with appropriate implementation"""
        pass


class ProductionRepositoryFactory(AbstractRepositoryFactory):
    """Production-ready repository factory with full features"""
    
    def create_user_repository(self, session: AsyncSession | None = None) -> IUserRepository:
        """Create production user repository"""
        from boursa_vision.infrastructure.persistence.repositories.user_repository import SQLAlchemyUserRepository
        return SQLAlchemyUserRepository(session)
    
    def create_portfolio_repository(self, session: AsyncSession | None = None) -> IPortfolioRepository:
        """Create production portfolio repository"""
        from boursa_vision.infrastructure.persistence.repositories.portfolio_repository import SQLAlchemyPortfolioRepository
        return SQLAlchemyPortfolioRepository(session)


class TestRepositoryFactory(AbstractRepositoryFactory):
    """Test-optimized repository factory for faster testing"""
    
    def create_user_repository(self, session: AsyncSession | None = None) -> IUserRepository:
        """Create test user repository with injected session"""
        from boursa_vision.infrastructure.persistence.repositories.user_repository import SQLAlchemyUserRepository
        
        if session is None:
            raise ValueError("Test repositories require an injected session")
        
        return SQLAlchemyUserRepository(session)
    
    def create_portfolio_repository(self, session: AsyncSession | None = None) -> IPortfolioRepository:
        """Create test portfolio repository with injected session"""
        from boursa_vision.infrastructure.persistence.repositories.portfolio_repository import SQLAlchemyPortfolioRepository
        
        if session is None:
            raise ValueError("Test repositories require an injected session")
            
        return SQLAlchemyPortfolioRepository(session)


class RepositoryFactoryProvider:
    """
    Singleton provider for repository factories
    Ensures consistent factory usage across application
    """
    
    _instance: RepositoryFactoryProvider | None = None
    _factory: AbstractRepositoryFactory | None = None
    
    def __new__(cls) -> RepositoryFactoryProvider:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def configure_factory(self, factory: AbstractRepositoryFactory) -> None:
        """Configure the repository factory to use"""
        self._factory = factory
    
    def get_factory(self) -> AbstractRepositoryFactory:
        """Get the configured factory or create default production factory"""
        if self._factory is None:
            self._factory = ProductionRepositoryFactory()
        return self._factory
    
    @classmethod
    def create_for_mode(cls, mode: RepositoryMode) -> AbstractRepositoryFactory:
        """Create factory for specific mode using pattern matching"""
        match mode:
            case RepositoryMode.PRODUCTION:
                return ProductionRepositoryFactory(mode)
            case RepositoryMode.TEST:
                return TestRepositoryFactory(mode)
            case RepositoryMode.SIMPLE:
                # Backwards compatibility - use production with simple mappers
                return ProductionRepositoryFactory(mode)
            case _:
                raise ValueError(f"Unsupported repository mode: {mode}")


# Convenience functions for common usage patterns
def create_repository_factory(mode: RepositoryMode | None = None) -> AbstractRepositoryFactory:
    """
    Create repository factory with optional mode specification
    Uses Python 3.13 pattern matching for clean logic
    """
    if mode is None:
        # Auto-detect based on environment
        import os
        mode = RepositoryMode.TEST if os.getenv("TESTING") else RepositoryMode.PRODUCTION
    
    return RepositoryFactoryProvider.create_for_mode(mode)


def get_default_factory() -> AbstractRepositoryFactory:
    """Get default repository factory instance"""
    return RepositoryFactoryProvider().get_factory()


# Example usage patterns
def example_usage():
    """Demonstrate modern repository factory usage"""

    # Production usage - demonstrating factory pattern
    production_factory = create_repository_factory(RepositoryMode.PRODUCTION)
    _ = production_factory.create_user_repository()
    _ = production_factory.create_portfolio_repository()

    # Test usage with session injection
    test_factory = create_repository_factory(RepositoryMode.TEST)

    # Pattern matching for error handling
    try:
        # Example: This would fail without session
        _ = test_factory.create_user_repository()
    except ValueError as e:
        match str(e):
            case s if "session" in s:
                print("Session injection required for test mode")
            case s if "mode" in s:
                print("Invalid repository mode specified")
            case _:
                print("Unknown repository error")


# Modern dependency injection helper
class RepositoryContainer:
    """
    Container for managing repository dependencies
    Uses Python 3.13 slots for better performance
    """
    __slots__ = ('_factory', '_portfolio_repository', '_user_repository')
    
    def __init__(self, factory: AbstractRepositoryFactory | None = None):
        self._factory = factory or get_default_factory()
        self._user_repository: IUserRepository | None = None
        self._portfolio_repository: IPortfolioRepository | None = None
    
    @property
    def user_repository(self) -> IUserRepository:
        """Lazy-loaded user repository"""
        if self._user_repository is None:
            self._user_repository = self._factory.create_user_repository()
        return self._user_repository
    
    @property
    def portfolio_repository(self) -> IPortfolioRepository:
        """Lazy-loaded portfolio repository"""
        if self._portfolio_repository is None:
            self._portfolio_repository = self._factory.create_portfolio_repository()
        return self._portfolio_repository
