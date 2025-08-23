"""
Database configuration and session management for the trading platform.

This module provides database configuration, session management, and connection pooling
optimized for PostgreSQL + TimescaleDB with SQLAlchemy 2.0.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration with optimized settings for PostgreSQL + TimescaleDB."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "trading_platform",
        username: str = "trading_user",
        password: str = "password",
        pool_size: int = 20,
        max_overflow: int = 30,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
    ):
        self.host = host
        self.port = port
        self.database = database
        self.username = username
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo

    @property
    def database_url(self) -> str:
        """Generate the async PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.username}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


class DatabaseManager:
    """
    Database manager with optimized connection pooling and session management.

    Provides async session management with proper connection pooling
    and TimescaleDB optimizations.
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None

    def create_engine(self) -> AsyncEngine:
        """Create and configure the async SQLAlchemy engine."""
        if self._engine is not None:
            return self._engine

        self._engine = create_async_engine(
            self.config.database_url,
            echo=self.config.echo,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            # PostgreSQL-specific optimizations
            connect_args={
                "server_settings": {
                    "jit": "off",  # Disable JIT for better performance on small queries
                    "application_name": "boursa_vision_backend",
                }
            },
        )

        # Add event listeners for performance monitoring
        self._setup_engine_events()

        return self._engine

    def _setup_engine_events(self) -> None:
        """Set up engine event listeners for monitoring and optimization."""
        if self._engine is None:
            return

        @event.listens_for(self._engine.sync_engine, "before_cursor_execute")
        def before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Log slow queries for performance monitoring."""
            logger.debug(f"Executing query: {statement[:100]}...")

    def create_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Create the async session factory."""
        if self._session_factory is not None:
            return self._session_factory

        engine = self.create_engine()
        self._session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False,
        )
        return self._session_factory

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get an async database session with proper cleanup.

        Usage:
            async with db_manager.get_session() as session:
                # Use session here
                pass
        """
        session_factory = self.create_session_factory()
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    async def ensure_timescale_extension(self) -> None:
        """Ensure TimescaleDB extension is enabled."""
        async with self.get_session() as session:
            try:
                # Check if extension is already installed
                result = await session.execute(
                    text(
                        "SELECT installed_version FROM pg_available_extensions "
                        "WHERE name='timescaledb'"
                    )
                )
                version = result.scalar_one_or_none()

                if version is None:
                    await session.execute(
                        text("CREATE EXTENSION IF NOT EXISTS timescaledb;")
                    )
                    await session.commit()
                    logger.info("TimescaleDB extension enabled")
                else:
                    logger.info(
                        f"TimescaleDB extension already installed (version: {version})"
                    )

            except Exception as e:
                logger.error(f"Failed to enable TimescaleDB extension: {e}")
                await session.rollback()
                raise

    async def create_hypertables(self) -> None:
        """Create TimescaleDB hypertables for time-series data."""
        hypertables = [
            {
                "table": "market_data",
                "time_column": "time",
                "chunk_interval": "1 day",
            },
            {
                "table": "technical_indicators",
                "time_column": "time",
                "chunk_interval": "1 day",
            },
            {
                "table": "signals",
                "time_column": "time",
                "chunk_interval": "1 day",
            },
            {
                "table": "portfolio_performance",
                "time_column": "time",
                "chunk_interval": "1 day",
            },
        ]

        async with self.get_session() as session:
            for ht in hypertables:
                try:
                    # First check if table exists
                    table_check = await session.execute(
                        text(
                            "SELECT 1 FROM information_schema.tables "
                            "WHERE table_name = :table_name AND table_schema = 'public'"
                        ),
                        {"table_name": ht["table"]},
                    )

                    if table_check.scalar_one_or_none() is None:
                        logger.info(
                            f"Table {ht['table']} does not exist, skipping hypertable creation"
                        )
                        continue

                    # Check if hypertable already exists
                    result = await session.execute(
                        text(
                            "SELECT 1 FROM timescaledb_information.hypertables "
                            "WHERE hypertable_name = :table_name"
                        ),
                        {"table_name": ht["table"]},
                    )

                    existing = result.scalar_one_or_none()
                    if not existing:
                        # Create hypertable
                        await session.execute(
                            text(
                                f"SELECT create_hypertable('{ht['table']}', "
                                f"'{ht['time_column']}', "
                                f"chunk_time_interval => INTERVAL '{ht['chunk_interval']}')"
                            )
                        )
                        logger.info(f"Created hypertable: {ht['table']}")
                    else:
                        logger.info(f"Hypertable already exists: {ht['table']}")

                except Exception as e:
                    logger.warning(f"Could not create hypertable {ht['table']}: {e}")
                    # Don't raise here, just log and continue

            await session.commit()

    async def close(self) -> None:
        """Close the database connection pool."""
        if self._engine is not None:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connection pool closed")
