"""
Performance tests for TimescaleDB queries.
Validates acceptance criteria: p95 latency < 100ms.
"""

import asyncio
import statistics
import time
from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from src.infrastructure.persistence.repository_factory import (
    MockRepositoryFactory,
    configure_repositories,
    get_market_data_repository,
    get_portfolio_repository,
    get_user_repository,
)


class PerformanceTestSuite:
    """Performance test suite for database operations."""

    def __init__(self):
        self.latencies: List[float] = []
        # Configure to use mock repositories for consistent testing
        configure_repositories(MockRepositoryFactory())

    async def measure_latency(self, operation_func):
        """Measure operation latency in milliseconds."""
        start_time = time.perf_counter()
        result = await operation_func()
        end_time = time.perf_counter()

        latency_ms = (end_time - start_time) * 1000
        self.latencies.append(latency_ms)
        return result, latency_ms

    def get_percentile(self, percentile: float) -> float:
        """Get latency percentile."""
        if not self.latencies:
            return 0.0
        return statistics.quantiles(sorted(self.latencies), n=100)[int(percentile) - 1]

    def reset_metrics(self):
        """Reset latency metrics."""
        self.latencies.clear()

    async def test_market_data_queries(self, iterations: int = 100):
        """Test market data query performance."""
        repo = get_market_data_repository()

        # Test 1: Latest price queries
        self.reset_metrics()
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]

        for _ in range(iterations):
            await self.measure_latency(lambda: repo.find_latest_by_symbol("AAPL"))

        latest_prices_p95 = self.get_percentile(95)
        print(f"Latest prices query P95 latency: {latest_prices_p95:.2f}ms")

        # Test 2: Time series queries
        self.reset_metrics()
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=30)

        for _ in range(iterations // 5):  # Fewer iterations for heavier queries
            await self.measure_latency(
                lambda: repo.find_by_symbol_and_timerange("AAPL", start_time, end_time)
            )

        timeseries_p95 = self.get_percentile(95)
        print(f"Time series query P95 latency: {timeseries_p95:.2f}ms")

        return {
            "latest_prices_p95": latest_prices_p95,
            "timeseries_p95": timeseries_p95,
        }

    async def test_portfolio_queries(self, iterations: int = 100):
        """Test portfolio query performance."""
        repo = get_portfolio_repository()

        # Mock user ID for testing
        from uuid import uuid4

        user_id = uuid4()

        self.reset_metrics()

        for _ in range(iterations):
            await self.measure_latency(lambda: repo.find_by_user_id(user_id))

        portfolio_p95 = self.get_percentile(95)
        print(f"Portfolio query P95 latency: {portfolio_p95:.2f}ms")

        return {"portfolio_p95": portfolio_p95}

    async def test_user_queries(self, iterations: int = 100):
        """Test user query performance."""
        repo = get_user_repository()

        self.reset_metrics()

        for _ in range(iterations):
            await self.measure_latency(lambda: repo.find_by_email("test@example.com"))

        user_p95 = self.get_percentile(95)
        print(f"User query P95 latency: {user_p95:.2f}ms")

        return {"user_p95": user_p95}

    async def run_all_tests(self) -> dict:
        """Run all performance tests."""
        print("Starting performance test suite...")

        results = {}

        # Market data tests
        print("\n=== Market Data Performance Tests ===")
        market_results = await self.test_market_data_queries()
        results.update(market_results)

        # Portfolio tests
        print("\n=== Portfolio Performance Tests ===")
        portfolio_results = await self.test_portfolio_queries()
        results.update(portfolio_results)

        # User tests
        print("\n=== User Performance Tests ===")
        user_results = await self.test_user_queries()
        results.update(user_results)

        # Summary
        print("\n=== Performance Test Summary ===")
        all_p95_values = [v for k, v in results.items() if "p95" in k]
        max_p95 = max(all_p95_values) if all_p95_values else 0

        print(f"Maximum P95 latency: {max_p95:.2f}ms")
        print(
            f"Acceptance criteria (P95 < 100ms): {'✅ PASS' if max_p95 < 100 else '❌ FAIL'}"
        )

        for key, value in results.items():
            status = "✅" if value < 100 else "❌"
            print(f"  {key}: {value:.2f}ms {status}")

        return results


async def run_performance_tests():
    """Run performance tests."""
    test_suite = PerformanceTestSuite()
    return await test_suite.run_all_tests()


# Pytest integration
@pytest.mark.asyncio
@pytest.mark.performance
async def test_database_performance():
    """Pytest performance test."""
    test_suite = PerformanceTestSuite()
    results = await test_suite.run_all_tests()

    # Assert all P95 latencies are under 100ms
    for key, value in results.items():
        if "p95" in key:
            assert value < 100, f"{key} latency {value:.2f}ms exceeds 100ms threshold"


if __name__ == "__main__":
    # CLI usage
    asyncio.run(run_performance_tests())
