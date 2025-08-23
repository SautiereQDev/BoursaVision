"""
SQLAlchemy persistence layer implementation.
Provides database access layer with TimescaleDB optimizations.
"""

from . import models

__all__ = ["models"]

from .initializer import (
    PersistenceLayerConfig,
    PersistenceLayerInitializer,
    create_persistence_context,
    init_persistence_layer,
    quick_setup,
)

# from .mappers import MapperFactory
from .repositories import (
    SQLAlchemyMarketDataRepository,
    SQLAlchemyPortfolioRepository,
    SQLAlchemyUserRepository,
)
from .repository_factory import (
    configure_repositories,
    get_market_data_repository,
    get_portfolio_repository,
    get_user_repository,
)
from .sqlalchemy.database import (
    DatabaseConfig,
    DatabaseManager,
    TimescaleDBManager,
    get_db_session,
)
from .unit_of_work import IUnitOfWork, SQLAlchemyUnitOfWork, get_uow

__all__ = [
    # Database management
    "DatabaseConfig",
    "DatabaseManager",
    # Mappers
    # "MapperFactory",
    # Unit of Work
    "IUnitOfWork",
    # Configuration and initialization
    "PersistenceLayerConfig",
    "PersistenceLayerInitializer",
    "SQLAlchemyMarketDataRepository",
    "SQLAlchemyPortfolioRepository",
    "SQLAlchemyUnitOfWork",
    # Repositories
    "SQLAlchemyUserRepository",
    "TimescaleDBManager",
    "configure_repositories",
    "create_persistence_context",
    "get_db_session",
    "get_market_data_repository",
    "get_portfolio_repository",
    "get_uow",
    "get_user_repository",
    "init_persistence_layer",
    # Models
    "models",
    "quick_setup",
]
