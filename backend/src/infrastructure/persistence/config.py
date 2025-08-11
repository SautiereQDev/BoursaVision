"""
Configuration and initialization for the persistence layer.

This module provides configuration classes and initialization logic
for setting up the complete persistence layer with PostgreSQL + TimescaleDB.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from .database import DatabaseConfig, DatabaseManager

logger = logging.getLogger(__name__)


# Load environment variables from .env file at project root
def load_env_file():
    """Load environment variables from .env file at project root."""
    # Find the project root (.env file location)
    current_path = Path(__file__).resolve()
    project_root = None

    # Search for .env file by going up the directory tree
    for parent in current_path.parents:
        env_file = parent / ".env"
        if env_file.exists():
            project_root = parent
            break

    if project_root:
        env_file = project_root / ".env"
        try:
            # Explicitly specify encoding
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        # Remove quotes if present
                        value = value.strip("\"'")
                        # Handle variable substitution like ${POSTGRES_USER}
                        if "${" in value and "}" in value:
                            # Simple variable substitution
                            import re

                            for match in re.finditer(r"\$\{([^}]+)\}", value):
                                var_name = match.group(1)
                                var_value = os.getenv(var_name, "")
                                value = value.replace(match.group(0), var_value)
                        os.environ[key] = value
            logger.info(f"Loaded environment variables from {env_file}")
        except Exception as e:
            logger.warning(f"Could not load .env file: {e}")
    else:
        logger.warning("No .env file found in project hierarchy")


# Load environment variables on module import
load_env_file()


class PersistenceConfig:
    """Configuration for the persistence layer."""

    def __init__(
        self,
        database_host: Optional[str] = None,
        database_port: Optional[int] = None,
        database_name: Optional[str] = None,
        database_user: Optional[str] = None,
        database_password: Optional[str] = None,
        pool_size: int = 20,
        max_overflow: int = 30,
        echo_sql: bool = False,
        enable_metrics: bool = True,
    ):
        # Use environment variables from .env file with fallbacks
        self.database_host = database_host or os.getenv("POSTGRES_HOST", "localhost")
        self.database_port = database_port or int(os.getenv("POSTGRES_PORT", "5432"))
        self.database_name = database_name or os.getenv("POSTGRES_DB", "boursa_vision")
        self.database_user = database_user or os.getenv("POSTGRES_USER", "boursa_user")
        self.database_password = database_password or os.getenv(
            "POSTGRES_PASSWORD", "boursa_dev_password_2024"
        )
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.echo_sql = (
            echo_sql or os.getenv("ENABLE_QUERY_DEBUGGING", "false").lower() == "true"
        )
        self.enable_metrics = enable_metrics

    def to_database_config(self) -> DatabaseConfig:
        """Convert to DatabaseConfig."""
        return DatabaseConfig(
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
            username=self.database_user,
            password=self.database_password,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
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

        except Exception as e:
            logger.error(f"Failed to initialize persistence layer: {e}")
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
        async with initializer.database_manager.get_session() as session:
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))
            return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def check_timescale_health() -> bool:
    """Check if TimescaleDB extension is working properly."""
    initializer = get_persistence_initializer()
    if not initializer or not initializer.is_initialized:
        return False

    try:
        async with initializer.database_manager.get_session() as session:
            from sqlalchemy import text

            result = await session.execute(
                text("SELECT count(*) FROM timescaledb_information.hypertables")
            )
            hypertable_count = result.scalar()
            return hypertable_count > 0
    except Exception as e:
        logger.error(f"TimescaleDB health check failed: {e}")
        return False
