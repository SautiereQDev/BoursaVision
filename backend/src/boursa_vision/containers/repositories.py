"""
Repository Container - Data Access Layer
========================================

RepositoryContainer manages all repository implementations with proper
dependency injection. This container provides factory functions for creating
repository instances aligned with existing implementations.

Features:
- Domain repository implementations (User, Portfolio, Investment)
- Market data repositories with TimescaleDB support
- Simplified factory functions matching existing constructors
- Clean separation of concerns

Dependencies: DatabaseContainer for session factories and connections
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


def _create_investment_repository(session_factory, cache_client):
    """Create investment repository with cache support."""
    from boursa_vision.infrastructure.persistence.repositories.investment_repository import (
        SQLAlchemyInvestmentRepository
    )
    return SQLAlchemyInvestmentRepository(
        session_factory=session_factory,
        cache_client=cache_client,
    )


def _create_position_repository(session_factory, cache_client):
    """Create position repository for portfolio positions."""
    from boursa_vision.infrastructure.persistence.repositories.position_repository import (
        SQLAlchemyPositionRepository
    )
    return SQLAlchemyPositionRepository(
        session_factory=session_factory,
        cache_client=cache_client,
    )


def _create_transaction_repository(session_factory):
    """Create transaction repository for financial transactions."""
    from boursa_vision.infrastructure.persistence.repositories.transaction_repository import (
        SQLAlchemyTransactionRepository
    )
    return SQLAlchemyTransactionRepository(session_factory=session_factory)


def _create_market_data_repository(session_factory, timeseries_engine, cache_client, redis_pubsub):
    """Create market data repository with TimescaleDB and real-time updates."""
    from boursa_vision.infrastructure.persistence.repositories.market_data_repository import (
        TimescaleMarketDataRepository
    )
    return TimescaleMarketDataRepository(
        session_factory=session_factory,
        timeseries_engine=timeseries_engine,
        cache_client=cache_client,
        redis_pubsub=redis_pubsub,
    )


def _create_market_data_timeline_repository(session_factory, timeseries_engine, cache_client):
    """Create market data timeline repository for time-series queries."""
    from boursa_vision.infrastructure.persistence.repositories.market_data_timeline_repository import (
        TimescaleMarketDataTimelineRepository
    )
    return TimescaleMarketDataTimelineRepository(
        session_factory=session_factory,
        timeseries_engine=timeseries_engine,
        cache_client=cache_client,
    )


def _create_fundamental_data_repository(session_factory, cache_client):
    """Create fundamental data repository for company financials."""
    from boursa_vision.infrastructure.persistence.repositories.fundamental_data_repository import (
        SQLAlchemyFundamentalDataRepository
    )
    return SQLAlchemyFundamentalDataRepository(
        session_factory=session_factory,
        cache_client=cache_client,
    )


def _create_technical_indicator_repository(session_factory, timeseries_engine):
    """Create technical indicator repository for trading signals."""
    from boursa_vision.infrastructure.persistence.repositories.technical_indicator_repository import (
        TimescaleTechnicalIndicatorRepository
    )
    return TimescaleTechnicalIndicatorRepository(
        session_factory=session_factory,
        timeseries_engine=timeseries_engine,
    )


def _create_refresh_token_repository(session_factory, cache_client):
    """Create refresh token repository with Redis cache for fast lookups."""
    from boursa_vision.infrastructure.persistence.repositories.refresh_token_repository import (
        SQLAlchemyRefreshTokenRepository
    )
    return SQLAlchemyRefreshTokenRepository(
        session_factory=session_factory,
        cache_client=cache_client,
    )


def _create_user_session_repository(session_factory, cache_client):
    """Create user session repository with Redis session storage."""
    from boursa_vision.infrastructure.persistence.repositories.user_session_repository import (
        RedisUserSessionRepository
    )
    return RedisUserSessionRepository(
        session_factory=session_factory,
        redis_client=cache_client,
    )


def _create_notification_repository(session_factory):
    """Create notification repository for user notifications."""
    from boursa_vision.infrastructure.persistence.repositories.notification_repository import (
        SQLAlchemyNotificationRepository
    )
    return SQLAlchemyNotificationRepository(session_factory=session_factory)


def _create_audit_log_repository(session_factory):
    """Create audit log repository for security and compliance tracking."""
    from boursa_vision.infrastructure.persistence.repositories.audit_log_repository import (
        SQLAlchemyAuditLogRepository
    )
    return SQLAlchemyAuditLogRepository(session_factory=session_factory)


def _create_system_config_repository(session_factory, cache_client):
    """Create system configuration repository with cache for performance."""
    from boursa_vision.infrastructure.persistence.repositories.system_config_repository import (
        SQLAlchemySystemConfigRepository
    )
    return SQLAlchemySystemConfigRepository(
        session_factory=session_factory,
        cache_client=cache_client,
    )


# =============================================================================
# REPOSITORY CONTAINER CLASS
# =============================================================================

class RepositoryContainer(containers.DeclarativeContainer):
    """
    Repository container for all data access layer implementations.
    
    Manages:
        - Domain repositories (User, Portfolio, Investment, etc.)
        - Market data repositories (TimescaleDB integration)
        - Cache-enhanced repositories for performance
        - Infrastructure repositories (RefreshToken, Notifications)
    
    All repositories follow Clean Architecture Repository Pattern
    with automatic dependency injection of sessions and cache clients.
    """
    
    # Dependencies injected from DatabaseContainer
    database = providers.DependenciesContainer()
    
    # =============================================================================
    # DOMAIN REPOSITORIES - Core business entities
    # =============================================================================
    
    user_repository = providers.Factory(
        _create_user_repository,
        session_factory=database.session_factory,
        cache_client=database.redis_cache,
    )
    
    portfolio_repository = providers.Factory(
        _create_portfolio_repository,
        session_factory=database.session_factory,
        cache_client=database.redis_cache,
        metrics_client=providers.Singleton(lambda: None),  # Will be injected later
    )
    
    investment_repository = providers.Factory(
        _create_investment_repository,
        session_factory=database.session_factory,
        cache_client=database.redis_cache,
    )
    
    position_repository = providers.Factory(
        _create_position_repository,
        session_factory=database.session_factory,
        cache_client=database.redis_cache,
    )
    
    transaction_repository = providers.Factory(
        _create_transaction_repository,
        session_factory=database.session_factory,
    )
    
    # =============================================================================
    # MARKET DATA REPOSITORIES - Time-series and financial data
    # =============================================================================
    
    market_data_repository = providers.Factory(
        _create_market_data_repository,
        session_factory=database.session_factory,
        timeseries_engine=database.timeseries_engine,
        cache_client=database.redis_cache,
        redis_pubsub=database.redis_pubsub,
    )
    
    market_data_timeline_repository = providers.Factory(
        _create_market_data_timeline_repository,
        session_factory=database.session_factory,
        timeseries_engine=database.timeseries_engine,
        cache_client=database.redis_cache,
    )
    
    fundamental_data_repository = providers.Factory(
        _create_fundamental_data_repository,
        session_factory=database.session_factory,
        cache_client=database.redis_cache,
    )
    
    technical_indicator_repository = providers.Factory(
        _create_technical_indicator_repository,
        session_factory=database.session_factory,
        timeseries_engine=database.timeseries_engine,
    )
    
    # =============================================================================
    # INFRASTRUCTURE REPOSITORIES - Authentication, sessions, etc.
    # =============================================================================
    
    refresh_token_repository = providers.Factory(
        _create_refresh_token_repository,
        session_factory=database.session_factory,
        cache_client=database.redis_cache,
    )
    
    user_session_repository = providers.Factory(
        _create_user_session_repository,
        session_factory=database.session_factory,
        cache_client=database.redis_session,
    )
    
    notification_repository = providers.Factory(
        _create_notification_repository,
        session_factory=database.session_factory,
    )
    
    audit_log_repository = providers.Factory(
        _create_audit_log_repository,
        session_factory=database.session_factory,
    )
    
    system_config_repository = providers.Factory(
        _create_system_config_repository,
        session_factory=database.session_factory,
        cache_client=database.redis_cache,
    )
