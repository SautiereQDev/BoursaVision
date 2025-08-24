"""
Repository Container - Data Access Layer (Clean)
===============================================

RepositoryContainer manages all repository implementations following
the Repository pattern. All repositories are aligned with existing
SQLAlchemy implementations in the codebase.

Features:
- Core domain repositories (User, Portfolio, Investment)
- TimescaleDB repositories for time-series data
- Repository pattern with clean interfaces
- Session and connection management
- Cache-enabled repositories for performance

Dependencies: DatabaseContainer (session factories, connections)
"""

from dependency_injector import containers, providers


# =============================================================================
# REPOSITORY FACTORY FUNCTIONS
# =============================================================================

def _create_user_repository(session_factory):
    """Create user repository aligned with existing SQLAlchemy implementation."""
    from boursa_vision.infrastructure.persistence.repositories import SqlAlchemyUserRepository
    return SqlAlchemyUserRepository(session=session_factory)


def _create_portfolio_repository(session_factory):
    """Create portfolio repository aligned with existing SQLAlchemy implementation."""
    from boursa_vision.infrastructure.persistence.repositories.portfolio_repository import SQLAlchemyPortfolioRepository
    return SQLAlchemyPortfolioRepository(session=session_factory)


def _create_investment_repository(session_factory):
    """Create investment repository aligned with existing SQLAlchemy implementation."""
    from boursa_vision.infrastructure.persistence.repositories.investment_repository import SQLAlchemyInvestmentRepository
    return SQLAlchemyInvestmentRepository(session=session_factory)


# =============================================================================
# REPOSITORY CONTAINER CLASS
# =============================================================================

class RepositoryContainer(containers.DeclarativeContainer):
    """
    Repository container for data access layer.
    
    Contains:
        - Core domain repositories (User, Portfolio, Investment)
        - TimescaleDB repositories for market data
        - Cache-enabled repositories for performance
        - Session factory dependency injection
    
    All repositories follow the Repository pattern with clean interfaces
    defined in the domain layer and implementations in infrastructure.
    """
    
    # Dependencies from DatabaseContainer
    session_factory = providers.DependenciesContainer()
    timescale_session_factory = providers.DependenciesContainer()
    redis_client = providers.DependenciesContainer()
    cache_client = providers.DependenciesContainer()
    
    # =============================================================================
    # CORE DOMAIN REPOSITORIES - User, Portfolio, Investment
    # =============================================================================
    
    user_repository = providers.Factory(
        _create_user_repository,
        session_factory=session_factory,
    )
    
    portfolio_repository = providers.Factory(
        _create_portfolio_repository,
        session_factory=session_factory,
    )
    
    investment_repository = providers.Factory(
        _create_investment_repository,
        session_factory=session_factory,
    )
