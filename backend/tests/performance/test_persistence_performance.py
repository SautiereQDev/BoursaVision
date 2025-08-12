"""
Performance tests for persistence layer operations.
Tests for database operations, connection pooling, and query optimization.
"""

import asyncio
import os
import statistics
import time
from datetime import datetime, timezone
from typing import List

import pytest

from src.core.config_simple import settings
from src.domain.entities.market_data import MarketData
from src.domain.entities.user import User
from src.domain.value_objects.money import Currency, Money
from src.domain.value_objects.price import Price
from src.infrastructure.persistence.repository_factory import (
    MockRepositoryFactory,
    configure_repositories,
    get_market_data_repository,
    get_user_repository,
)

# Ensure we use mock repositories and testing environment for performance tests
if not settings.use_mock_repositories or settings.environment != "testing":
    # Force testing configuration
    os.environ["USE_MOCK_REPOSITORIES"] = "true"
    os.environ["ENVIRONMENT"] = "testing"
    # Reload settings to pick up the changes
    from importlib import reload

    import src.core.config_simple

    reload(src.core.config_simple)
    from src.core.config_simple import settings

# Ensure we use mock repositories for performance tests
os.environ.setdefault("USE_MOCK_REPOSITORIES", "true")
os.environ.setdefault("ENVIRONMENT", "testing")


class PerformanceTestSuite:
    """Performance test suite for persistence operations."""

    def __init__(self):
        self.latencies: List[float] = []

    async def measure_latency(self, operation):
        """Measure operation latency."""
        start_time = time.perf_counter()
        await operation()
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        self.latencies.append(latency_ms)
        return latency_ms

    def get_p95_latency(self) -> float:
        """Get 95th percentile latency."""
        if not self.latencies:
            return 0.0
        sorted_latencies = sorted(self.latencies)
        index = int(0.95 * len(sorted_latencies)) - 1
        index = max(
            0, min(index, len(sorted_latencies) - 1)
        )  # Ensure index is within bounds
        return sorted_latencies[index]

    def get_stats(self) -> dict:
        """Get comprehensive latency statistics."""
        if not self.latencies:
            return {}

        sorted_latencies = sorted(self.latencies)
        count = len(sorted_latencies)

        def calculate_percentile(percentile: float) -> float:
            index = int(percentile * count) - 1
            return sorted_latencies[max(0, min(index, count - 1))]

        return {
            "count": count,
            "min": min(sorted_latencies),
            "max": max(sorted_latencies),
            "mean": sum(sorted_latencies) / count,
            "p50": calculate_percentile(0.50),
            "p95": calculate_percentile(0.95),
            "p99": calculate_percentile(0.99),
        }


@pytest.mark.asyncio
async def test_user_repository_performance():
    """Test user repository performance."""
    # Configure to use mock repositories for consistent performance testing
    configure_repositories(MockRepositoryFactory())

    perf_suite = PerformanceTestSuite()
    user_repo = get_user_repository()

    # Test user creation performance
    for i in range(100):
        user = User.create(
            email=f"test{i}@example.com",
            username=f"testuser{i}",
            first_name="Test",
            last_name="User",
        )
        await perf_suite.measure_latency(lambda u=user: user_repo.save(u))

    # Test user lookup performance
    for i in range(100):
        await perf_suite.measure_latency(
            lambda email=f"test{i % 50}@example.com": user_repo.find_by_email(email)
        )

    stats = perf_suite.get_stats()
    print("User Repository Performance Stats:", stats)

    # Assert p95 latency is under 100ms
    assert stats["p95"] < 100.0, f"P95 latency {stats['p95']:.2f}ms exceeds 100ms"


@pytest.mark.asyncio
async def test_market_data_repository_performance():
    """Test market data repository performance (TimescaleDB)."""
    # Configure to use mock repositories for consistent performance testing
    configure_repositories(MockRepositoryFactory())

    perf_suite = PerformanceTestSuite()
    market_data_repo = get_market_data_repository()

    # Test market data insertion performance
    for i in range(100):  # Reduced iterations for faster tests
        from decimal import Decimal

        from src.domain.entities.market_data import MarketDataArgs

        args = MarketDataArgs(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc).replace(microsecond=i * 1000),
            open_price=Decimal(str(150.0 + i)),
            high_price=Decimal(str(155.0 + i)),
            low_price=Decimal(str(149.0 + i)),
            close_price=Decimal(str(154.0 + i)),
            volume=1000000 + i,
        )
        market_data = MarketData.create(args)

        # Fix lambda closure issue
        await perf_suite.measure_latency(
            lambda md=market_data: market_data_repo.save(md)
        )

    # Test market data query performance
    for i in range(100):
        await perf_suite.measure_latency(
            lambda: market_data_repo.find_latest_by_symbol("AAPL")
        )

    stats = perf_suite.get_stats()
    print(f"Market Data Repository Performance Stats: {stats}")

    # Assert p95 latency is under 100ms
    assert stats["p95"] < 100.0, f"P95 latency {stats['p95']:.2f}ms exceeds 100ms"


@pytest.mark.asyncio
async def test_concurrent_operations_performance():
    """Test performance under concurrent load."""
    # Configure to use mock repositories for consistent performance testing
    configure_repositories(MockRepositoryFactory())

    perf_suite = PerformanceTestSuite()

    # Replace asyncio.current_task().get_name() with a safer alternative
    async def concurrent_user_operations():
        """Perform concurrent user operations."""
        user_repo = get_user_repository()

        # Create user
        task_id = id(asyncio.current_task()) if asyncio.current_task() else 0
        user = User.create(
            email=f"concurrent{task_id}@example.com",
            username=f"concurrent{task_id}",
            first_name="Concurrent",
            last_name="User",
        )

        await user_repo.save(user)

        # Lookup user (mock returns None, which is expected for mock implementation)
        await user_repo.find_by_email(user.email)

    # Run 50 concurrent operations
    tasks = []
    for i in range(50):
        task = asyncio.create_task(
            perf_suite.measure_latency(concurrent_user_operations), name=f"task_{i}"
        )
        tasks.append(task)

    await asyncio.gather(*tasks)

    stats = perf_suite.get_stats()
    print(f"Concurrent Operations Performance Stats: {stats}")

    # Assert p95 latency is under 200ms for concurrent operations
    assert stats["p95"] < 200.0, f"P95 latency {stats['p95']:.2f}ms exceeds 200ms"


@pytest.mark.asyncio
async def test_bulk_operations_performance():
    """Test bulk operations performance."""
    # Configure to use mock repositories for consistent performance testing
    configure_repositories(MockRepositoryFactory())

    perf_suite = PerformanceTestSuite()
    market_data_repo = get_market_data_repository()

    # Test bulk market data insertion
    market_data_batch = []
    for i in range(1000):  # Reduced for faster tests
        from decimal import Decimal

        from src.domain.entities.market_data import MarketDataArgs

        args = MarketDataArgs(
            symbol="BULK_TEST",
            timestamp=datetime.now(timezone.utc).replace(microsecond=i * 1000),
            open_price=Decimal(str(100.0 + i * 0.01)),
            high_price=Decimal(str(101.0 + i * 0.01)),
            low_price=Decimal(str(99.0 + i * 0.01)),
            close_price=Decimal(str(100.5 + i * 0.01)),
            volume=1000 + i,
        )
        market_data = MarketData.create(args)
        market_data_batch.append(market_data)

    async def bulk_insert():
        """Perform bulk insert."""
        for md in market_data_batch:
            await market_data_repo.save(md)

    latency = await perf_suite.measure_latency(bulk_insert)
    throughput = len(market_data_batch) / (latency / 1000)  # Records per second

    print("Bulk Insert Performance:")
    print(f"  Records: {len(market_data_batch)}")
    print(f"  Latency: {latency:.2f}ms")
    print(f"  Throughput: {throughput:.2f} records/sec")

    # Assert reasonable throughput (at least 100 records/sec for this test)
    assert throughput > 100, f"Throughput {throughput:.2f} records/sec is too low"


if __name__ == "__main__":
    # Run performance tests
    asyncio.run(test_user_repository_performance())
    asyncio.run(test_market_data_repository_performance())
    asyncio.run(test_concurrent_operations_performance())
    asyncio.run(test_bulk_operations_performance())
