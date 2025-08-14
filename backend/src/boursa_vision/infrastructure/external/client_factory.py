"""
YFinance Client Factory
======================

Factory for creating optimized YFinance clients with different configurations.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from .cache_strategy import CacheConfig
from .yfinance_client import OptimizedYFinanceClient, YFinanceConfig


class ClientProfile(Enum):
    """Predefined client profiles for different use cases"""

    DEVELOPMENT = "development"  # Low rate limits, logging enabled
    PRODUCTION = "production"  # Optimized for production use
    HIGH_FREQUENCY = "high_frequency"  # Maximum performance for HFT
    RESEARCH = "research"  # Balanced for research workloads
    TESTING = "testing"  # Minimal resources for testing


@dataclass
class ClientFactoryConfig:
    """Factory configuration"""

    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    enable_cache: bool = True
    cache_key_prefix: str = "boursa_vision:"


class YFinanceClientFactory:
    """
    Factory for creating optimized YFinance clients.

    Implements the Factory pattern to create clients with different configurations
    based on use case profiles.
    """

    def __init__(self, factory_config: Optional[ClientFactoryConfig] = None):
        self.factory_config = factory_config or ClientFactoryConfig()

    def create_client(
        self,
        profile: ClientProfile = ClientProfile.PRODUCTION,
        custom_config: Optional[YFinanceConfig] = None,
    ) -> OptimizedYFinanceClient:
        """
        Create a YFinance client based on profile or custom configuration.

        Args:
            profile: Predefined configuration profile
            custom_config: Custom configuration (overrides profile)

        Returns:
            Configured OptimizedYFinanceClient
        """
        if custom_config:
            return OptimizedYFinanceClient(custom_config)

        config = self._get_profile_config(profile)
        return OptimizedYFinanceClient(config)

    def _get_profile_config(self, profile: ClientProfile) -> YFinanceConfig:
        """Get configuration for specific profile"""
        if profile == ClientProfile.DEVELOPMENT:
            return self._create_development_config()
        if profile == ClientProfile.PRODUCTION:
            return self._create_production_config()
        if profile == ClientProfile.HIGH_FREQUENCY:
            return self._create_high_frequency_config()
        if profile == ClientProfile.RESEARCH:
            return self._create_research_config()
        if profile == ClientProfile.TESTING:
            return self._create_testing_config()
        raise ValueError(f"Unknown profile: {profile}")

    def _create_development_config(self) -> YFinanceConfig:
        """Configuration for development environment"""
        cache_config = self._create_cache_config()

        return YFinanceConfig(
            max_requests_per_minute=500,  # Conservative rate limit
            max_concurrent_requests=10,
            batch_size=5,
            request_timeout=30.0,
            max_retries=3,
            retry_base_delay=1.0,
            retry_max_delay=30.0,
            circuit_breaker_failure_threshold=3,
            circuit_breaker_recovery_timeout=30.0,
            enable_cache=self.factory_config.enable_cache,
            cache_config=cache_config,
        )

    def _create_production_config(self) -> YFinanceConfig:
        """Configuration for production environment"""
        cache_config = self._create_cache_config()

        return YFinanceConfig(
            max_requests_per_minute=1800,  # Near API limit with buffer
            max_concurrent_requests=50,
            batch_size=20,
            request_timeout=30.0,
            max_retries=5,
            retry_base_delay=1.0,
            retry_max_delay=60.0,
            circuit_breaker_failure_threshold=5,
            circuit_breaker_recovery_timeout=60.0,
            enable_cache=self.factory_config.enable_cache,
            cache_config=cache_config,
        )

    def _create_high_frequency_config(self) -> YFinanceConfig:
        """Configuration for high-frequency trading"""
        cache_config = self._create_cache_config()
        # Aggressive cache settings for HFT
        cache_config.ttl_real_time = 15  # 15 seconds for real-time data
        cache_config.ttl_intraday = 60  # 1 minute for intraday

        return YFinanceConfig(
            max_requests_per_minute=1950,  # Maximum possible
            max_concurrent_requests=100,
            batch_size=50,
            request_timeout=10.0,  # Shorter timeout
            max_retries=2,  # Fewer retries for speed
            retry_base_delay=0.5,
            retry_max_delay=5.0,
            circuit_breaker_failure_threshold=10,
            circuit_breaker_recovery_timeout=30.0,
            enable_cache=True,  # Always enabled for HFT
            cache_config=cache_config,
        )

    def _create_research_config(self) -> YFinanceConfig:
        """Configuration for research workloads"""
        cache_config = self._create_cache_config()
        # Longer cache times for research
        cache_config.ttl_daily = 7200  # 2 hours
        cache_config.ttl_weekly = 86400  # 24 hours
        cache_config.ttl_monthly = 604800  # 1 week

        return YFinanceConfig(
            max_requests_per_minute=1000,
            max_concurrent_requests=25,
            batch_size=15,
            request_timeout=60.0,  # Longer timeout for large datasets
            max_retries=5,
            retry_base_delay=2.0,
            retry_max_delay=120.0,
            circuit_breaker_failure_threshold=8,
            circuit_breaker_recovery_timeout=90.0,
            enable_cache=self.factory_config.enable_cache,
            cache_config=cache_config,
        )

    def _create_testing_config(self) -> YFinanceConfig:
        """Configuration for testing environment"""
        cache_config = self._create_cache_config()
        cache_config.db = 15  # Use different Redis DB for testing

        return YFinanceConfig(
            max_requests_per_minute=60,  # Very conservative
            max_concurrent_requests=3,
            batch_size=2,
            request_timeout=10.0,
            max_retries=1,
            retry_base_delay=0.5,
            retry_max_delay=5.0,
            circuit_breaker_failure_threshold=2,
            circuit_breaker_recovery_timeout=10.0,
            enable_cache=False,  # Usually disabled for testing
            cache_config=cache_config,
        )

    def _create_cache_config(self) -> CacheConfig:
        """Create cache configuration from factory config"""
        return CacheConfig(
            host=self.factory_config.redis_host,
            port=self.factory_config.redis_port,
            db=self.factory_config.redis_db,
            password=self.factory_config.redis_password,
            key_prefix=self.factory_config.cache_key_prefix,
        )

    @classmethod
    def create_development_client(
        cls, factory_config: Optional[ClientFactoryConfig] = None
    ) -> OptimizedYFinanceClient:
        """Convenience method for creating development client"""
        factory = cls(factory_config)
        return factory.create_client(ClientProfile.DEVELOPMENT)

    @classmethod
    def create_production_client(
        cls, factory_config: Optional[ClientFactoryConfig] = None
    ) -> OptimizedYFinanceClient:
        """Convenience method for creating production client"""
        factory = cls(factory_config)
        return factory.create_client(ClientProfile.PRODUCTION)

    @classmethod
    def create_testing_client(
        cls, factory_config: Optional[ClientFactoryConfig] = None
    ) -> OptimizedYFinanceClient:
        """Convenience method for creating testing client"""
        factory = cls(factory_config)
        return factory.create_client(ClientProfile.TESTING)


# Convenience functions for quick client creation
def create_development_client() -> OptimizedYFinanceClient:
    """Create client optimized for development"""
    return YFinanceClientFactory.create_development_client()


def create_production_client() -> OptimizedYFinanceClient:
    """Create client optimized for production"""
    return YFinanceClientFactory.create_production_client()


def create_testing_client() -> OptimizedYFinanceClient:
    """Create client optimized for testing"""
    return YFinanceClientFactory.create_testing_client()


def create_high_frequency_client() -> OptimizedYFinanceClient:
    """Create client optimized for high-frequency trading"""
    factory = YFinanceClientFactory()
    return factory.create_client(ClientProfile.HIGH_FREQUENCY)


def create_research_client() -> OptimizedYFinanceClient:
    """Create client optimized for research workloads"""
    factory = YFinanceClientFactory()
    return factory.create_client(ClientProfile.RESEARCH)
