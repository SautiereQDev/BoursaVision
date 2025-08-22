"""
Configuration et initialisation pour la couche de persistance.

Ce module fournit les classes de configuration et la logique d'initialisation
pour configurer la couche de persistance complète avec PostgreSQL + TimescaleDB.

Utilise maintenant la configuration globale centralisée.
"""

import logging
from typing import Optional

import sqlalchemy

from ...core.config_simple import settings
from .database import DatabaseConfig, DatabaseManager

logger = logging.getLogger(__name__)


# Initialize configuration
# load_env_file()  # Removed: now handled by global config


class PersistenceConfig:
    """Configuration for the persistence layer using global settings."""

    def __init__(self, **overrides):
        """Initialize persistence configuration using global settings."""
        # Use global settings with optional overrides
        self.database_url = overrides.get("database_url", settings.database_url)
        self.database_host = overrides.get("database_host", settings.postgres_host)
        self.database_port = overrides.get("database_port", settings.postgres_port)
        self.database_name = overrides.get("database_name", settings.postgres_db)
        self.database_user = overrides.get("database_user", settings.postgres_user)
        self.database_password = overrides.get(
            "database_password", settings.postgres_password
        )

        # Development settings
        self.echo_sql = overrides.get("echo_sql", settings.debug)

        # Pool configuration
        self.pool_size = overrides.get("pool_size", settings.db_pool_size)
        self.pool_overflow = overrides.get("pool_overflow", settings.db_pool_overflow)
        self.pool_timeout = overrides.get("pool_timeout", settings.db_pool_timeout)

    def to_database_config(self) -> DatabaseConfig:
        """Convert to DatabaseConfig."""
        return DatabaseConfig(
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
            username=self.database_user,
            password=self.database_password,
            pool_size=self.pool_size,
            max_overflow=self.pool_overflow,
            echo=self.echo_sql,
        )


class PersistenceInitializer:
    """
    Initializer for the complete persistence layer.

    Sets up database connections, repositories, and all related components.
    """

    def __init__(self, config: PersistenceConfig):
        self.config = config
        self._db_manager: Optional[DatabaseManager] = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize the persistence layer."""
        if self._is_initialized:
            logger.warning("Persistence layer already initialized")
            return

        try:
            # Initialize database manager
            db_config = self.config.to_database_config()
            self._db_manager = DatabaseManager(db_config)

            # Create engine and session factory
            self._db_manager.create_engine()
            session_factory = self._db_manager.create_session_factory()

            # Ensure TimescaleDB is properly configured
            await self._db_manager.ensure_timescale_extension()
            await self._db_manager.create_hypertables()

            # Set up repository factory provider
            from .factory import RepositoryFactoryProvider, repository_registry

            factory_provider = RepositoryFactoryProvider(session_factory)
            repository_registry.register_factory_provider(factory_provider)

            self._is_initialized = True
            logger.info("Persistence layer initialized successfully")

        except (ConnectionError, ImportError, RuntimeError) as e:
            logger.error("Failed to initialize persistence layer: %s", e)
            raise

    async def shutdown(self) -> None:
        """Shutdown the persistence layer."""
        if self._db_manager:
            await self._db_manager.close()
            self._db_manager = None

        self._is_initialized = False
        logger.info("Persistence layer shutdown completed")

    @property
    def is_initialized(self) -> bool:
        """Check if persistence layer is initialized."""
        return self._is_initialized

    @property
    def database_manager(self) -> Optional[DatabaseManager]:
        """Get the database manager."""
        return self._db_manager


# Global persistence initializer instance
_persistence_initializer: Optional[PersistenceInitializer] = None


def get_persistence_initializer() -> Optional[PersistenceInitializer]:
    """Get the global persistence initializer."""
    return _persistence_initializer


def set_persistence_initializer(initializer: PersistenceInitializer) -> None:
    """Set the global persistence initializer."""
    # pylint: disable=global-statement
    global _persistence_initializer
    _persistence_initializer = initializer


async def initialize_persistence(config: PersistenceConfig) -> PersistenceInitializer:
    """Initialize the persistence layer with the given configuration."""
    initializer = PersistenceInitializer(config)
    await initializer.initialize()
    set_persistence_initializer(initializer)
    return initializer


async def shutdown_persistence() -> None:
    """Shutdown the persistence layer."""
    # pylint: disable=global-statement
    global _persistence_initializer
    if _persistence_initializer:
        await _persistence_initializer.shutdown()
        _persistence_initializer = None


# Context manager for persistence lifecycle
class PersistenceContext:
    """Context manager for persistence layer lifecycle."""

    def __init__(self, config: PersistenceConfig):
        self.config = config
        self._initializer: Optional[PersistenceInitializer] = None

    async def __aenter__(self) -> PersistenceInitializer:
        """Initialize persistence layer."""
        self._initializer = await initialize_persistence(self.config)
        return self._initializer

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Shutdown persistence layer."""
        await shutdown_persistence()


# Health check functions
async def check_database_health() -> bool:
    """Check if database is healthy and accessible."""
    initializer = get_persistence_initializer()
    if not initializer or not initializer.is_initialized:
        return False

    try:
        if initializer.database_manager is None:
            logger.error("Database manager is not initialized")
            return False

        if initializer.database_manager is None:
            logger.error("Database manager is not initialized")
            return False

        async with initializer.database_manager.get_session() as session:
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))
            return True
    except (ConnectionError, sqlalchemy.exc.SQLAlchemyError) as e:
        logger.error("Database health check failed: %s", e)
        return False


async def check_timescale_health() -> bool:
    """Check if TimescaleDB extension is working properly."""
    initializer = get_persistence_initializer()
    if not initializer or not initializer.is_initialized:
        return False

    try:
        if initializer.database_manager is None:
            logger.error("Database manager is not initialized")
            return False

        async with initializer.database_manager.get_session() as session:
            from sqlalchemy import text

            result = await session.execute(
                text("SELECT count(*) FROM timescaledb_information.hypertables")
            )
            hypertable_count = result.scalar()
            return hypertable_count is not None and hypertable_count > 0
    except (ConnectionError, sqlalchemy.exc.SQLAlchemyError) as e:
        logger.error("TimescaleDB health check failed: %s", e)
        return False
