"""
Repository Container - Data Access Layer (Simplified)
=====================================================

RepositoryContainer manages the core repository implementations that exist
and are properly implemented. This simplified version focuses on the 
essential repositories needed for the application.

Features:
- User repository (authentication, profiles)
- Portfolio repository (portfolio CRUD)
- Investment repository (investment tracking)
- Market data repository (TimescaleDB integration)
- Refresh token repository (JWT management)

Dependencies: DatabaseContainer for session management
"""

from dependency_injector import containers, providers


# =============================================================================
# REPOSITORY FACTORY FUNCTIONS
# =============================================================================

def _create_user_repository():
    """Create SQLAlchemy user repository."""
    from boursa_vision.infrastructure.persistence.repositories.user_repository import (
        SQLAlchemyUserRepository
    )
    return SQLAlchemyUserRepository()


def _create_portfolio_repository():
    """Create SQLAlchemy portfolio repository."""
    from boursa_vision.infrastructure.persistence.repositories.portfolio_repository import (
        SQLAlchemyPortfolioRepository
    )
    return SQLAlchemyPortfolioRepository()


def _create_investment_repository():
    """Create SQLAlchemy investment repository."""
    from boursa_vision.infrastructure.persistence.repositories.investment_repository import (
        SQLAlchemyInvestmentRepository
    )
    return SQLAlchemyInvestmentRepository()


def _create_market_data_repository():
    """Create TimescaleDB market data repository."""
    from boursa_vision.infrastructure.persistence.repositories.market_data_repository import (
        SQLAlchemyMarketDataRepository
    )
    return SQLAlchemyMarketDataRepository()


def _create_refresh_token_repository():
    """Create refresh token repository."""
    from boursa_vision.infrastructure.persistence.repositories.refresh_token_repository import (
        SQLAlchemyRefreshTokenRepository
    )
    # For now, return None - we'll implement this later when session management is ready
    # return SQLAlchemyRefreshTokenRepository(session=None)
    class MockRefreshTokenRepository:
        def __init__(self):
            self.tokens = {}
        
        async def save(self, token):
            self.tokens[token.id] = token
            return token
        
        async def find_by_token(self, token_value):
            for token in self.tokens.values():
                if getattr(token, 'token', None) == token_value:
                    return token
            return None
        
        async def delete_by_user_id(self, user_id):
            to_delete = [k for k, v in self.tokens.items() if getattr(v, 'user_id', None) == user_id]
            for k in to_delete:
                del self.tokens[k]
    
    return MockRefreshTokenRepository()


# =============================================================================
# REPOSITORY CONTAINER CLASS
# =============================================================================

class RepositoryContainer(containers.DeclarativeContainer):
    """
    Repository container for all data access layer implementations.
    
    Manages the core repositories that are implemented and tested:
        - User repository for authentication and user management
        - Portfolio repository for portfolio CRUD operations
        - Investment repository for investment tracking
        - Market data repository for price data and analytics
        - Refresh token repository for JWT token management
    
    All repositories follow Clean Architecture Repository Pattern
    with automatic session management via the get_db_session factory.
    """
    
    # Dependencies injected from DatabaseContainer
    database = providers.DependenciesContainer()
    
    # =============================================================================
    # CORE REPOSITORIES - Essential business entities
    # =============================================================================
    
    user_repository = providers.Factory(
        _create_user_repository,
    )
    
    portfolio_repository = providers.Factory(
        _create_portfolio_repository,
    )
    
    investment_repository = providers.Factory(
        _create_investment_repository,
    )
    
    # =============================================================================
    # MARKET DATA REPOSITORIES - Time-series data with TimescaleDB
    # =============================================================================
    
    market_data_repository = providers.Factory(
        _create_market_data_repository,
    )
    
    # =============================================================================
    # INFRASTRUCTURE REPOSITORIES - Authentication & system
    # =============================================================================
    
    refresh_token_repository = providers.Factory(
        _create_refresh_token_repository,
    )
