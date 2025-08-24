"""
Database Container - Database Connections and Session Management
==============================================================

DatabaseContainer manages all database-related infrastructure:
- PostgreSQL connection pools with optimized settings
- TimescaleDB connections for time-series data
- Multiple Redis connections (cache, sessions, pub/sub)
- Session factories with proper lifecycle management
- Resource providers for automatic cleanup

This container depends on CoreContainer for configuration.
"""

from typing import Any
import asyncio

from dependency_injector import containers, providers


# =============================================================================
# DATABASE FACTORY FUNCTIONS
# =============================================================================

async def _create_async_database_engine(
    url: str,
    pool_size: int = 10,
    max_overflow: int = 20,
    pool_timeout: int = 30,
    pool_recycle: int = 3600,
    echo: bool = False,
) -> "AsyncEngine":
    """
    Create optimized async SQLAlchemy engine for PostgreSQL.
    
    Args:
        url: Database connection URL
        pool_size: Number of connections to maintain in pool
        max_overflow: Additional connections beyond pool_size
        pool_timeout: Timeout for getting connection from pool
        pool_recycle: Seconds before connection is recycled
        echo: Enable SQL query logging
        
    Returns:
        Configured async SQLAlchemy engine
    """
    # In Phase 1, we create a mock engine
    # In later phases, this will use real SQLAlchemy
    return _MockAsyncEngine(url=url, pool_size=pool_size, echo=echo)


def _create_async_session_factory(engine: "AsyncEngine") -> "AsyncSessionFactory":
    """Create async session factory bound to the engine."""
    return _MockAsyncSessionFactory(engine=engine)


async def _create_timescale_engine(
    url: str,
    pool_size: int = 5,
    echo: bool = False,
) -> "AsyncEngine":
    """
    Create TimescaleDB connection for time-series market data.
    
    TimescaleDB is optimized for time-series data with automatic partitioning
    and compression. Used specifically for market data storage.
    """
    return _MockTimescaleEngine(url=url, pool_size=pool_size, echo=echo)


async def _create_redis_connection(
    url: str,
    decode_responses: bool = True,
    max_connections: int = 50,
    socket_timeout: int = 5,
    socket_connect_timeout: int = 5,
    retry_on_timeout: bool = False,
) -> "RedisConnection":
    """
    Create Redis connection with optimized settings.
    
    Args:
        url: Redis connection URL
        decode_responses: Whether to decode byte responses to strings
        max_connections: Maximum connections in the pool
        socket_timeout: Timeout for socket operations
        socket_connect_timeout: Timeout for connection establishment
        retry_on_timeout: Whether to retry operations on timeout
        
    Returns:
        Configured Redis connection
    """
    return _MockRedisConnection(
        url=url,
        decode_responses=decode_responses,
        max_connections=max_connections,
    )


# =============================================================================
# MOCK IMPLEMENTATIONS (Phase 1 - will be replaced with real implementations)
# =============================================================================

class _MockAsyncEngine:
    """Mock async SQLAlchemy engine for Phase 1."""
    
    def __init__(self, url: str, pool_size: int, echo: bool):
        self.url = url
        self.pool_size = pool_size
        self.echo = echo
        self._closed = False
    
    async def dispose(self) -> None:
        """Clean up engine resources."""
        self._closed = True
    
    def __repr__(self) -> str:
        return f"MockAsyncEngine(url='{self.url}', pool_size={self.pool_size})"


class _MockAsyncSessionFactory:
    """Mock async session factory for Phase 1."""
    
    def __init__(self, engine: _MockAsyncEngine):
        self.engine = engine
    
    def __call__(self) -> "MockAsyncSession":
        return _MockAsyncSession(engine=self.engine)


class _MockAsyncSession:
    """Mock async session for Phase 1."""
    
    def __init__(self, engine: _MockAsyncEngine):
        self.engine = engine
        self._closed = False
    
    async def __aenter__(self) -> "_MockAsyncSession":
        return self
    
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()
    
    async def close(self) -> None:
        """Close the session."""
        self._closed = True
    
    async def commit(self) -> None:
        """Commit the transaction."""
        pass  # Mock implementation
    
    async def rollback(self) -> None:
        """Rollback the transaction."""
        pass  # Mock implementation


class _MockTimescaleEngine(_MockAsyncEngine):
    """Mock TimescaleDB engine for Phase 1."""
    
    def __repr__(self) -> str:
        return f"MockTimescaleEngine(url='{self.url}', pool_size={self.pool_size})"


class _MockRedisConnection:
    """Mock Redis connection for Phase 1."""
    
    def __init__(self, url: str, decode_responses: bool, max_connections: int):
        self.url = url
        self.decode_responses = decode_responses
        self.max_connections = max_connections
        self._closed = False
        self._data: dict[str, Any] = {}
    
    async def close(self) -> None:
        """Close Redis connection."""
        self._closed = True
    
    async def get(self, key: str) -> Any:
        """Get value by key."""
        return self._data.get(key)
    
    async def set(self, key: str, value: Any, ex: int | None = None) -> bool:
        """Set key-value pair with optional expiration."""
        self._data[key] = value
        return True
    
    async def delete(self, *keys: str) -> int:
        """Delete keys."""
        deleted = 0
        for key in keys:
            if key in self._data:
                del self._data[key]
                deleted += 1
        return deleted
    
    async def ping(self) -> bool:
        """Test connection."""
        return not self._closed
    
    def __repr__(self) -> str:
        return f"MockRedisConnection(url='{self.url}', decode_responses={self.decode_responses})"


# =============================================================================
# DATABASE CONTAINER CLASS
# =============================================================================

class DatabaseContainer(containers.DeclarativeContainer):
    """
    Database container for all data persistence infrastructure.
    
    Provides:
        - PostgreSQL async connection pool
        - TimescaleDB connection for time-series data
        - Redis connections (cache, sessions, pub/sub)
        - Session factories with proper lifecycle
        - Resource providers for cleanup
    """
    
    # Configuration from CoreContainer
    config = providers.Configuration()
    
    # PostgreSQL connection pool (main database)
    database_engine = providers.Resource(
        _create_async_database_engine,
        url=config.database.url,
        pool_size=config.database.pool_size.as_(int, default=10),
        max_overflow=config.database.max_overflow.as_(int, default=20),
        pool_timeout=config.database.pool_timeout.as_(int, default=30),
        pool_recycle=config.database.pool_recycle.as_(int, default=3600),
        echo=config.database.echo.as_(bool, default=False),
    )
    
    # Session factory for SQLAlchemy
    session_factory = providers.Factory(
        _create_async_session_factory,
        engine=database_engine,
    )
    
    # TimescaleDB connection for market data time-series
    timescale_engine = providers.Resource(
        _create_timescale_engine,
        url=config.timescale.url,
        pool_size=config.timescale.pool_size.as_(int, default=5),
        echo=config.timescale.echo.as_(bool, default=False),
    )
    
    # Redis connections with different purposes
    
    # Redis for caching (decode_responses=True for string data)
    redis_cache = providers.Resource(
        _create_redis_connection,
        url=config.redis.cache_url,
        decode_responses=True,
        max_connections=config.redis.cache_max_connections.as_(int, default=50),
        socket_timeout=config.redis.socket_timeout.as_(int, default=5),
        socket_connect_timeout=config.redis.connect_timeout.as_(int, default=5),
        retry_on_timeout=True,
    )
    
    # Redis for sessions (decode_responses=False for binary data)
    redis_sessions = providers.Resource(
        _create_redis_connection,
        url=config.redis.sessions_url,
        decode_responses=False,
        max_connections=config.redis.sessions_max_connections.as_(int, default=20),
        socket_timeout=config.redis.socket_timeout.as_(int, default=5),
    )
    
    # Redis for pub/sub messaging (WebSocket, notifications)
    redis_pubsub = providers.Resource(
        _create_redis_connection,
        url=config.redis.pubsub_url,
        decode_responses=True,
        max_connections=config.redis.pubsub_max_connections.as_(int, default=10),
        socket_timeout=config.redis.socket_timeout.as_(int, default=10),
    )
