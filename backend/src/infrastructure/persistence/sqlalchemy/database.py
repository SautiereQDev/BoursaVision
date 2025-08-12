"""
Database configuration and session management for SQLAlchemy with TimescaleDB.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy import MetaData, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool, QueuePool

from application.exceptions import DatabaseNotInitializedError

from ..models.base import Base

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration with connection pooling optimization."""

    def __init__(
        self,
        url: str,
        pool_size: int = 20,
        max_overflow: int = 10,
        pool_timeout: int = 30,
        pool_recycle: int = 3600,
        echo: bool = False,
    ):
        self.url = url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.pool_recycle = pool_recycle
        self.echo = echo


class DatabaseManager:
    """
    Database manager implementing connection pooling and session management.
    Optimized for high-performance queries with TimescaleDB.
    """

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None

    async def initialize(self) -> None:
        """Initialize database engine and session factory."""
        if self._engine is not None:
            return

        # Create optimized engine for TimescaleDB
        self._engine = create_async_engine(
            self.config.url,
            poolclass=QueuePool,
            pool_size=self.config.pool_size,
            max_overflow=self.config.max_overflow,
            pool_timeout=self.config.pool_timeout,
            pool_recycle=self.config.pool_recycle,
            echo=self.config.echo,
            # TimescaleDB optimizations
            connect_args={
                "server_settings": {
                    "jit": "off",  # Disable JIT for better performance with time-series
                    "shared_preload_libraries": "timescaledb",
                }
            },
        )

        # Register connection events for TimescaleDB
        @event.listens_for(self._engine.sync_engine, "connect")
        def set_timescaledb_settings(dbapi_connection, connection_record):
            """Set TimescaleDB-specific settings on connection."""
            with dbapi_connection.cursor() as cursor:
                # Optimize for time-series queries
                cursor.execute("SET timescaledb.enable_optimizations = 'on'")
                cursor.execute("SET work_mem = '256MB'")
                cursor.execute("SET random_page_cost = 1.1")
                cursor.execute("SET effective_cache_size = '2GB'")

        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )

        logger.info("Database engine initialized successfully")

    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
            logger.info("Database connections closed")

    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if self._engine is None:
            raise DatabaseNotInitializedError()
        return self._engine

    @property
    def session_factory(self) -> async_sessionmaker:
        """Get session factory."""
        if self._session_factory is None:
            raise DatabaseNotInitializedError()
        return self._session_factory

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Create database session with proper error handling."""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


class TimescaleDBManager:
    """Manager for TimescaleDB-specific operations."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    async def create_hypertables(self) -> None:
        """Create TimescaleDB hypertables for time-series data."""
        hypertables = [
            {
                "table": "market_data",
                "time_column": "time",
                "chunk_time_interval": "1 day",
                "partition_column": "symbol",
            },
            {
                "table": "technical_indicators",
                "time_column": "time",
                "chunk_time_interval": "1 day",
                "partition_column": "symbol",
            },
            {
                "table": "signals",
                "time_column": "time",
                "chunk_time_interval": "1 day",
                "partition_column": "symbol",
            },
            {
                "table": "portfolio_performance",
                "time_column": "time",
                "chunk_time_interval": "1 day",
                "partition_column": "portfolio_id",
            },
        ]

        async with self.db_manager.session() as session:
            for hypertable in hypertables:
                try:
                    # Check if hypertable already exists
                    result = await session.execute(
                        text(
                            "SELECT hypertable_name FROM timescaledb_information.hypertables WHERE hypertable_name = :table"
                        ),
                        {"table": hypertable["table"]},
                    )

                    if result.fetchone() is None:
                        # Create hypertable
                        if "partition_column" in hypertable:
                            sql = text(
                                f"SELECT create_hypertable('{hypertable['table']}', "
                                f"'{hypertable['time_column']}', "
                                f"partitioning_column => '{hypertable['partition_column']}', "
                                f"number_partitions => 4, "
                                f"chunk_time_interval => INTERVAL '{hypertable['chunk_time_interval']}')"
                            )
                        else:
                            sql = text(
                                f"SELECT create_hypertable('{hypertable['table']}', "
                                f"'{hypertable['time_column']}', "
                                f"chunk_time_interval => INTERVAL '{hypertable['chunk_time_interval']}')"
                            )

                        await session.execute(sql)
                        logger.info(f"Created hypertable: {hypertable['table']}")
                    else:
                        logger.info(f"Hypertable already exists: {hypertable['table']}")

                except Exception as e:
                    logger.error(
                        f"Error creating hypertable {hypertable['table']}: {e}"
                    )
                    raise

    async def create_performance_indexes(self) -> None:
        """Create performance indexes for time-series queries."""
        indexes = [
            # Market data indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_market_data_symbol_time_desc ON market_data (symbol, time DESC)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_market_data_volume ON market_data (volume) WHERE volume > 0",
            # Technical indicators indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_technical_indicators_symbol_type_time ON technical_indicators (symbol, indicator_type, time DESC)",
            # Signals indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signals_symbol_strength_time ON signals (symbol, signal_strength, time DESC)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_signals_type_time ON signals (signal_type, time DESC)",
            # Portfolio performance indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_portfolio_performance_portfolio_time ON portfolio_performance (portfolio_id, time DESC)",
            # Composite indexes for common queries
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_market_data_symbol_interval_time ON market_data (symbol, interval_type, time DESC)",
        ]

        async with self.db_manager.session() as session:
            for index_sql in indexes:
                try:
                    await session.execute(text(index_sql))
                    logger.info(
                        f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}"
                    )
                except Exception as e:
                    logger.warning(f"Index creation failed or already exists: {e}")

    async def setup_compression(self) -> None:
        """Set up compression policies for time-series data."""
        compression_policies = [
            {"table": "market_data", "compress_after": "7 days"},
            {"table": "technical_indicators", "compress_after": "7 days"},
            {"table": "signals", "compress_after": "30 days"},
            {"table": "portfolio_performance", "compress_after": "30 days"},
        ]

        async with self.db_manager.session() as session:
            for policy in compression_policies:
                try:
                    sql = text(
                        f"SELECT add_compression_policy('{policy['table']}', "
                        f"INTERVAL '{policy['compress_after']}')"
                    )
                    await session.execute(sql)
                    logger.info(f"Added compression policy for {policy['table']}")
                except Exception as e:
                    logger.warning(
                        f"Compression policy already exists for {policy['table']}: {e}"
                    )


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None
_timescale_manager: Optional[TimescaleDBManager] = None


def init_database(config: DatabaseConfig) -> None:
    """Initialize global database manager."""
    global _db_manager, _timescale_manager
    _db_manager = DatabaseManager(config)
    _timescale_manager = TimescaleDBManager(_db_manager)


def get_db_manager() -> DatabaseManager:
    """Get global database manager."""
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_manager


def get_timescale_manager() -> TimescaleDBManager:
    """Get global TimescaleDB manager."""
    if _timescale_manager is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _timescale_manager


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session from global manager."""
    db_manager = get_db_manager()
    async with db_manager.session() as session:
        yield session
