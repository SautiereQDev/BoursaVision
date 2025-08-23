"""
Cache Strategy Implementation
============================

Redis-based caching with adaptive TTL for YFinance data.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field  # Removed unused `asdict`
from datetime import datetime
from enum import Enum
from typing import Any  # Reintroduced `Any` import

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class DataFrequency(Enum):
    """
    Enumeration of data frequency types for adaptive TTL.

    Attributes:
        REAL_TIME: Real-time data (TTL of 30 seconds).
        INTRADAY: Intraday data (TTL of 5 minutes).
        DAILY: Daily data (TTL of 1 hour).
        WEEKLY: Weekly data (TTL of 6 hours).
        MONTHLY: Monthly data (TTL of 24 hours).
    """

    REAL_TIME = "real_time"  # 30 seconds
    INTRADAY = "intraday"  # 5 minutes
    DAILY = "daily"  # 1 hour
    WEEKLY = "weekly"  # 6 hours
    MONTHLY = "monthly"  # 24 hours


@dataclass
class CacheConfig:
    """Cache configuration"""

    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: str | None = None
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    health_check_interval: int = 30
    max_connections: int = 10

    # TTL settings (grouped into a dictionary to reduce attributes)
    ttl_settings: dict[str, int] = field(
        default_factory=lambda: {
            "real_time": 30,
            "intraday": 300,
            "daily": 3600,
            "weekly": 21600,
            "monthly": 86400,
        }
    )

    # Cache key prefix
    key_prefix: str = "boursa_vision:"


class CacheStrategy(ABC):
    """Abstract cache strategy"""

    @abstractmethod
    def get_ttl(self, frequency: DataFrequency) -> int:
        """Get TTL for given data frequency"""
        ...

    @abstractmethod
    def should_cache(self, data: Any) -> bool:
        """Determine if data should be cached"""
        ...


class AdaptiveCacheStrategy(CacheStrategy):
    """
    Adaptive cache strategy that adjusts TTL based on data frequency
    and market conditions.
    """

    def __init__(self, config: CacheConfig):
        self.config = config
        self._market_hours_ttl_multiplier = 0.5  # Reduce TTL during market hours

    def get_ttl(self, frequency: DataFrequency) -> int:
        """Get adaptive TTL based on frequency and market conditions"""
        base_ttl = {
            DataFrequency.REAL_TIME: self.config.ttl_settings["real_time"],
            DataFrequency.INTRADAY: self.config.ttl_settings["intraday"],
            DataFrequency.DAILY: self.config.ttl_settings["daily"],
            DataFrequency.WEEKLY: self.config.ttl_settings["weekly"],
            DataFrequency.MONTHLY: self.config.ttl_settings["monthly"],
        }[frequency]

        # Adjust TTL based on market hours
        if self._is_market_hours():
            return int(base_ttl * self._market_hours_ttl_multiplier)

        return base_ttl

    def should_cache(self, data: Any) -> bool:
        """Determine if data should be cached"""
        if data is None:
            return False

        # Don't cache empty datasets
        return not (isinstance(data, list | dict) and len(data) == 0)

    def _is_market_hours(self) -> bool:
        """Check if current time is during market hours (simplified)"""
        now = datetime.now()
        weekday = now.weekday()
        hour = now.hour

        # Simple check: Monday-Friday, 9:30 AM - 4:00 PM ET
        # This should be enhanced with proper timezone handling
        if weekday >= 5:  # Weekend
            return False

        return 9 <= hour <= 16


class RedisCache:
    """
    Redis-based cache implementation with connection pooling and error handling.

    Implements the Facade pattern to simplify Redis operations.
    """

    def __init__(self, config: CacheConfig, strategy: CacheStrategy):
        self.config = config
        self.strategy = strategy
        self._pool = None
        self._redis = None
        self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize Redis connection with pool"""
        try:
            self._pool = redis.ConnectionPool(
                host=self.config.host,
                port=self.config.port,
                db=self.config.db,
                password=self.config.password,
                socket_timeout=self.config.socket_timeout,
                socket_connect_timeout=self.config.socket_connect_timeout,
                health_check_interval=self.config.health_check_interval,
                max_connections=self.config.max_connections,
                decode_responses=True,
            )
            self._redis = redis.Redis(connection_pool=self._pool)

            # Test connection
            self._redis.ping()
            logger.info("Redis cache initialized successfully")

        except RedisError as e:
            logger.error("Cache error: %s", e)
            self._redis = None

    def get(self, key: str) -> Any | None:
        """Get value from cache"""
        if not self._redis:
            return None

        try:
            full_key = self._build_key(key)
            cached_data = self._redis.get(full_key)

            if cached_data:
                return json.loads(cached_data)

        except (RedisError, json.JSONDecodeError) as e:
            logger.warning("Cache get error for key %s: %s", key, e)

        return None

    def set(
        self, key: str, value: Any, frequency: DataFrequency = DataFrequency.DAILY
    ) -> bool:
        """Set value in cache with adaptive TTL"""
        if not self._redis or not self.strategy.should_cache(value):
            return False

        try:
            full_key = self._build_key(key)
            ttl = self.strategy.get_ttl(frequency)

            serialized_value = json.dumps(value, default=str)
            self._redis.setex(full_key, ttl, serialized_value)

            logger.debug(f"Cached key {key} with TTL {ttl}s")
            return True

        except (
            RedisError,
            TypeError,
        ) as e:  # Replaced `json.JSONEncodeError` with `TypeError`
            logger.warning("Cache set error for key %s: %s", key, e)
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self._redis:
            return False

        try:
            full_key = self._build_key(key)
            result = self._redis.delete(full_key)
            return result > 0

        except RedisError as e:
            logger.warning("Cache delete error for key %s: %s", key, e)
            return False

    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self._redis:
            return False

        try:
            full_key = self._build_key(key)
            return self._redis.exists(full_key) > 0

        except RedisError as e:
            logger.warning("Cache exists error for key %s: %s", key, e)
            return False

    def get_ttl(self, key: str) -> int | None:
        """Get remaining TTL for key"""
        if not self._redis:
            return None

        try:
            full_key = self._build_key(key)
            ttl = self._redis.ttl(full_key)
            return ttl if ttl > 0 else None

        except RedisError as e:
            logger.warning("Cache TTL error for key %s: %s", key, e)
            return None

    def flush_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self._redis:
            return 0

        try:
            full_pattern = self._build_key(pattern)
            keys = self._redis.keys(full_pattern)

            if keys:
                return self._redis.delete(*keys)
            return 0

        except RedisError as e:
            logger.warning("Cache flush pattern error for %s: %s", pattern, e)
            return 0

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics"""
        if not self._redis:
            return {"status": "disconnected"}

        try:
            info = self._redis.info()
            return {
                "status": "connected",
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0), info.get("keyspace_misses", 0)
                ),
            }

        except RedisError as e:
            logger.warning("Cache stats error: %s", e)
            return {"status": "error", "error": str(e)}

    def _build_key(self, key: str) -> str:
        """Build full cache key with prefix"""
        return f"{self.config.key_prefix}{key}"

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage"""
        total = hits + misses
        return (hits / total * 100) if total > 0 else 0.0

    def is_healthy(self) -> bool:
        """Check if cache is healthy"""
        if not self._redis:
            return False

        try:
            self._redis.ping()
            return True
        except RedisError:
            return False


class CacheKeyBuilder:
    """
    Helper class for building standardized cache keys.

    Implements the Builder pattern for cache key construction.
    """

    def __init__(self, base_key: str = ""):
        self.parts = [base_key] if base_key else []

    def add_symbol(self, symbol: str) -> "CacheKeyBuilder":
        """Add symbol to key"""
        self.parts.append(f"symbol:{symbol}")
        return self

    def add_timeframe(
        self, period: str, interval: str | None = None
    ) -> "CacheKeyBuilder":
        """Add timeframe to key"""
        if interval:
            self.parts.append(f"timeframe:{period}:{interval}")
        else:
            self.parts.append(f"timeframe:{period}")
        return self

    def add_data_type(self, data_type: str) -> "CacheKeyBuilder":
        """Add data type to key"""
        self.parts.append(f"type:{data_type}")
        return self

    def add_date(self, date: str | datetime) -> "CacheKeyBuilder":
        """Add date to key"""
        date_str = date.strftime("%Y-%m-%d") if isinstance(date, datetime) else date
        self.parts.append(f"date:{date_str}")
        return self

    def add_custom(self, key: str, value: str) -> "CacheKeyBuilder":
        """Add custom key-value pair"""
        self.parts.append(f"{key}:{value}")
        return self

    def build(self) -> str:
        """Build the final cache key"""
        return ":".join(self.parts)

    def reset(self) -> "CacheKeyBuilder":
        """Reset builder to empty state"""
        self.parts.clear()
        return self

    @classmethod
    def for_price_data(
        cls, symbol: str, period: str, interval: str | None = None
    ) -> str:
        """Build cache key for price data"""
        builder = cls("price_data")
        return builder.add_symbol(symbol).add_timeframe(period, interval).build()

    @classmethod
    def for_fundamental_data(cls, symbol: str) -> str:
        """Build cache key for fundamental data"""
        builder = cls("fundamental_data")
        return builder.add_symbol(symbol).build()

    @classmethod
    def for_technical_indicators(cls, symbol: str, indicator: str, period: str) -> str:
        """Build cache key for technical indicators"""
        builder = cls("technical_indicators")
        return (
            builder.add_symbol(symbol)
            .add_custom("indicator", indicator)
            .add_timeframe(period)
            .build()
        )
