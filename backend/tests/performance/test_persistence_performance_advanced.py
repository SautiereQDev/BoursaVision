"""
Performance Testing for Persistence Layer
=========================================

This script tests the performance of the persistence layer to ensure
it meets the acceptance criteria:
- P95 latency < 100ms for critical queries

Tests include:
- Latest prices queries (5 symbols) - Target: < 15ms
- Time series queries (30 days) - Target: < 45ms  
- Portfolio queries - Target: < 8ms
- User queries - Target: < 5ms
"""

import asyncio
import logging
import statistics
import time
from datetime import datetime, timedelta

from typing import Dict, List

from src.infrastructure.persistence.repository_factory import get_market_data_repository, get_portfolio_repository, get_user_repository

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}
    
    def record_latency(self, operation: str, latency_ms: float):
        """Record latency for an operation."""
        if operation not in self.metrics:
            self.metrics[operation] = []
        self.metrics[operation].append(latency_ms)
    
    def get_statistics(self, operation: str) -> Dict[str, float]:
        """Get statistics for an operation."""
        if operation not in self.metrics:
            return {}
        
        latencies = self.metrics[operation]
        return {
            "count": len(latencies),
            "min": min(latencies),
            "max": max(latencies),
            "mean": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p95": self._percentile(latencies, 95),
            "p99": self._percentile(latencies, 99),
        }
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile."""
        sorted_data = sorted(data)
        index = int((percentile / 100) * len(sorted_data))
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def print_summary(self):
        """Print performance summary."""
        logger.info("=" * 60)
        logger.info("PERFORMANCE SUMMARY")
        logger.info("=" * 60)
        
        for operation, _ in self.metrics.items():
            stats = self.get_statistics(operation)
            logger.info("\n%s:", operation)
            logger.info("  Count: %d", stats['count'])
            logger.info("  Mean: %.2fms", stats['mean'])
            logger.info("  Median: %.2fms", stats['median'])
            logger.info("  P95: %.2fms", stats['p95'])
            logger.info("  P99: %.2fms", stats['p99'])
            logger.info("  Min: %.2fms", stats['min'])
            logger.info("  Max: %.2fms", stats['max'])
            # Check acceptance criteria
            p95 = stats['p95']
            if p95 < 100:
                logger.info("  ✅ PASS - P95 (%.2fms) < 100ms", p95)
            else:
                logger.warning("  ❌ FAIL - P95 (%.2fms) >= 100ms", p95)


async def time_operation(operation_name: str, operation_func, monitor: PerformanceMonitor, *args, **kwargs):
    """Time an async operation and record the latency."""
    start_time = time.perf_counter()
    
    try:
        result = await operation_func(*args, **kwargs)
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        monitor.record_latency(operation_name, latency_ms)
        return result
    except Exception as e:
        end_time = time.perf_counter()
        latency_ms = (end_time - start_time) * 1000
        logger.warning("Operation %s failed after %.2fms: %s", operation_name, latency_ms, e)
        # Still record the latency even for failed operations
        monitor.record_latency(f"{operation_name}_FAILED", latency_ms)
        raise


async def _run_user_queries(monitor: PerformanceMonitor, iterations: int = 100):
    """Test user query performance."""
    logger.info("Testing user queries (%d iterations)...", iterations)
    
    user_repo = get_user_repository()
    
    # Test find by email (should be very fast with index)
    for i in range(iterations):
        await time_operation(
            "user_find_by_email",
            user_repo.find_by_email,
            monitor,
            f"test{i % 10}@example.com"  # Cycle through 10 emails
        )
    
    # Test find active users
    for i in range(iterations // 10):  # Fewer iterations for bulk queries
        await time_operation(
            "user_find_active",
            user_repo.find_active_users,
            monitor
        )


async def _run_portfolio_queries(monitor: PerformanceMonitor, iterations: int = 100):
    """Test portfolio query performance."""
    logger.info("Testing portfolio queries (%d iterations)...", iterations)
    
    portfolio_repo = get_portfolio_repository()
    
    # Test find by user ID
    for i in range(iterations):
        # Use mock UUIDs or existing ones
        fake_user_id = f"12345678-1234-1234-1234-{i:012d}"
        await time_operation(
            "portfolio_find_by_user_id",
            portfolio_repo.find_by_user_id,
            monitor,
            fake_user_id
        )


async def _run_market_data_queries(monitor: PerformanceMonitor, iterations: int = 50):
    """Test market data query performance (TimescaleDB)."""
    logger.info("Testing market data queries (%d iterations)...", iterations)
    
    market_data_repo = get_market_data_repository()
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
    
    # Test latest prices for multiple symbols (Target: ~15ms)
    for i in range(iterations):
        await time_operation(
            "market_data_latest_prices_5_symbols",
            market_data_repo.find_latest_by_symbols,
            monitor,
            symbols
        )

    # Test time series queries (30 days) (Target: ~45ms)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    for i in range(iterations // 2):  # Fewer iterations for heavy queries
        symbol = symbols[i % len(symbols)]
        await time_operation(
            "market_data_time_series_30_days",
            market_data_repo.find_by_symbol,
            monitor,
            symbol,
            start_date,
            end_date
        )
    
    # Test latest by symbol
    for i in range(iterations):
        symbol = symbols[i % len(symbols)]
        await time_operation(
            "market_data_latest_by_symbol",
            market_data_repo.find_latest_by_symbol,
            monitor,
            symbol
        )


async def _run_concurrent_operations(monitor: PerformanceMonitor, concurrent_requests: int = 10):
    """Test concurrent operation performance."""
    logger.info("Testing concurrent operations (%d concurrent)...", concurrent_requests)
    
    market_data_repo = get_market_data_repository()
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
    
    # Create concurrent tasks
    tasks = []
    for i in range(concurrent_requests):
        symbol = symbols[i % len(symbols)]
        task = time_operation(
            "concurrent_latest_by_symbol",
            market_data_repo.find_latest_by_symbol,
            monitor,
            symbol
        )
        tasks.append(task)
    
    # Execute all tasks concurrently
    start_time = time.perf_counter()
    results = await asyncio.gather(*tasks, return_exceptions=True)
    end_time = time.perf_counter()
    
    total_time_ms = (end_time - start_time) * 1000
    logger.info("Concurrent execution completed in %.2fms", total_time_ms)
    
    # Count successful results
    successful = sum(1 for r in results if not isinstance(r, Exception))
    logger.info("Successful concurrent operations: %d/%d", successful, concurrent_requests)


async def run_stress_test(monitor: PerformanceMonitor, duration_seconds: int = 30):
    """Run a stress test for a specific duration."""
    logger.info("Running stress test for %d seconds...", duration_seconds)
    
    market_data_repo = get_market_data_repository()
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"]
    
    start_time = time.time()
    operation_count = 0
    
    while time.time() - start_time < duration_seconds:
        symbol = symbols[operation_count % len(symbols)]
        
        try:
            await time_operation(
                "stress_test_operation",
                market_data_repo.find_latest_by_symbol,
                monitor,
                symbol
            )
            operation_count += 1
        except Exception as e:
            logger.warning("Stress test operation failed: %s", e)
        
        # Small delay to prevent overwhelming the system
        await asyncio.sleep(0.01)
    
    total_time = time.time() - start_time
    throughput = operation_count / total_time
    
    logger.info("Stress test completed:")
    logger.info("  Operations: %d", operation_count)
    logger.info("  Duration: %.2fs", total_time)
    logger.info("  Throughput: %.2f ops/sec", throughput)


def validate_acceptance_criteria(monitor: PerformanceMonitor) -> bool:
    """Validate that performance meets acceptance criteria."""
    logger.info("\nValidating acceptance criteria...")
    
    criteria = {
        "market_data_latest_prices_5_symbols": 15.0,  # Target: < 15ms
        "market_data_time_series_30_days": 45.0,      # Target: < 45ms
        "portfolio_find_by_user_id": 8.0,             # Target: < 8ms
        "user_find_by_email": 5.0,                    # Target: < 5ms
    }
    
    all_passed = True
    
    for operation, target_ms in criteria.items():
        if operation in monitor.metrics:
            stats = monitor.get_statistics(operation)
            p95 = stats['p95']
            
            if p95 <= target_ms:
                logger.info("✅ %s: P95 %.2fms <= %.2fms", operation, p95, target_ms)
            else:
                logger.warning("❌ %s: P95 %.2fms > %.2fms", operation, p95, target_ms)
                all_passed = False
        else:
            logger.warning("⚠️ %s: No data collected", operation)
            all_passed = False
    
    # Overall acceptance criteria: P95 < 100ms for all operations
    for operation, _ in monitor.metrics.items():
        stats = monitor.get_statistics(operation)
        p95 = stats['p95']
        if p95 >= 100:
            logger.warning("❌ %s: P95 %.2fms >= 100ms (fails acceptance criteria)", operation, p95)
            all_passed = False
    
    return all_passed



# Pytest entrypoint
import pytest

@pytest.mark.asyncio
async def test_persistence_performance_advanced():
    """Pytest-compatible entrypoint for advanced persistence performance tests."""
    logger.info("Starting Performance Testing Suite")
    logger.info("=" * 60)

    monitor = PerformanceMonitor()

    try:
        # Run all performance tests
        await _run_user_queries(monitor, iterations=100)
        await _run_portfolio_queries(monitor, iterations=100)
        await _run_market_data_queries(monitor, iterations=50)
        await _run_concurrent_operations(monitor, concurrent_requests=20)
        await run_stress_test(monitor, duration_seconds=10)

        # Print summary
        monitor.print_summary()

        # Validate acceptance criteria
        criteria_passed = validate_acceptance_criteria(monitor)

        if criteria_passed:
            logger.info("\n🎉 ALL ACCEPTANCE CRITERIA PASSED!")
            logger.info("The persistence layer meets performance requirements.")
        else:
            logger.warning("\n⚠️ SOME ACCEPTANCE CRITERIA FAILED!")
            logger.warning("Performance optimization may be needed.")

        assert criteria_passed, "Some acceptance criteria failed. See logs for details."

    except Exception as e:
        logger.error("Performance testing failed: %s", e)
        raise



