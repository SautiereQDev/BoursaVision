"""
Persistence layer initialization and configuration.
Sets up database connections, repositories, and Unit of Work.
"""

import logging

from boursa_vision.infrastructure.persistence.repository_factory import (
    SQLAlchemyRepositoryFactory,
    configure_repositories,
)
from boursa_vision.infrastructure.persistence.sqlalchemy.database import (
    DatabaseConfig,
    DatabaseManager,
    TimescaleDBManager,
    get_db_manager,
    get_timescale_manager,
    init_database,
)
from boursa_vision.infrastructure.persistence.unit_of_work import (
    UnitOfWorkFactory,
    init_uow_factory,
)

logger = logging.getLogger(__name__)


class PersistenceLayerConfig:
    """Configuration for the persistence layer."""

    def __init__(
        self,
        database_url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
        create_hypertables: bool = True,
        create_indexes: bool = True,
        setup_compression: bool = True,
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.create_hypertables = create_hypertables
        self.create_indexes = create_indexes
        self.setup_compression = setup_compression


class PersistenceLayerInitializer:
    """
    Initializes and manages the persistence layer components.

    This class is responsible for setting up database connections,
    repositories, and other persistence layer components.
    """

    def __init__(self, config: PersistenceLayerConfig):
        """Initialize with configuration."""
        self.config = config
        self.db_manager: DatabaseManager | None = None
        self.timescale_manager: TimescaleDBManager | None = None
        self.repository_factory: SQLAlchemyRepositoryFactory | None = None
        self.uow_factory: UnitOfWorkFactory | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all persistence layer components."""
        if self._initialized:
            return

        logger.info("Initializing persistence layer...")

        # Initialize database
        db_config = DatabaseConfig(
            url=self.config.database_url,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            echo=self.config.echo,
        )

        init_database(db_config)
        self.db_manager = get_db_manager()
        self.timescale_manager = get_timescale_manager()

        # Initialize repositories
        self.repository_factory = SQLAlchemyRepositoryFactory()
        configure_repositories(self.repository_factory)

        # Initialize Unit of Work
        self.uow_factory = UnitOfWorkFactory()
        init_uow_factory(self.uow_factory)

        # Setup TimescaleDB features if requested
        if self.config.create_hypertables:
            await self._setup_timescale_features()

        self._initialized = True
        logger.info("Persistence layer initialized successfully")

    async def _setup_timescale_features(self) -> None:
        """Setup TimescaleDB-specific features."""
        if not self.timescale_manager:
            return

        # This would be implemented based on your TimescaleDB setup needs
        # For now, we'll just log that it's being set up
        logger.info("Setting up TimescaleDB features...")

    async def shutdown(self) -> None:
        """Shutdown persistence layer and clean up resources."""
        if not self._initialized:
            return

        logger.info("Shutting down persistence layer...")

        if self.db_manager:
            await self.db_manager.close()

        self._initialized = False
        logger.info("Persistence layer shutdown complete")

    @property
    def is_initialized(self) -> bool:
        """Check if the persistence layer is initialized."""
        return self._initialized


# Global initializer instance
_initializer: PersistenceLayerInitializer | None = None


def init_persistence_layer(
    config: PersistenceLayerConfig,
) -> PersistenceLayerInitializer:
    """Initialize persistence layer with configuration."""
    # pylint: disable=global-statement
    global _initializer
    _initializer = PersistenceLayerInitializer(config)
    return _initializer


def get_persistence_initializer() -> PersistenceLayerInitializer | None:
    """Get the global persistence layer initializer."""
    return _initializer


async def quick_setup(database_url: str, **kwargs) -> None:
    """
    Quick setup for development/testing.

    Args:
        database_url: PostgreSQL+TimescaleDB connection URL
        **kwargs: Additional configuration options
    """
    config = PersistenceLayerConfig(database_url, **kwargs)
    initializer = init_persistence_layer(config)
    await initializer.initialize()


# Context manager for easy setup/teardown
class PersistenceContext:
    """Context manager for persistence layer lifecycle."""

    def __init__(self, config: PersistenceLayerConfig):
        self.config = config
        self.initializer = None

    async def __aenter__(self):
        """Enter context and initialize persistence layer."""
        self.initializer = init_persistence_layer(self.config)
        await self.initializer.initialize()
        return self.initializer

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit context and shutdown persistence layer."""
        if self.initializer:
            await self.initializer.shutdown()


def create_persistence_context(database_url: str, **kwargs) -> PersistenceContext:
    """Create persistence context for async with usage."""
    config = PersistenceLayerConfig(database_url, **kwargs)
    return PersistenceContext(config)
