"""
Example usage and configuration for the persistence layer.

This module demonstrates how to configure and use the persistence layer
in a real application.
"""

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add the backend src directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.domain.entities.user import User, UserRole
from src.domain.value_objects.money import Currency
from src.infrastructure.persistence.config import (
    PersistenceConfig,
    initialize_persistence,
    shutdown_persistence,
)
from src.infrastructure.persistence.factory import repository_registry
from src.infrastructure.persistence.uow import AutoTransaction

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_usage():
    """Example of basic persistence layer usage."""

    # 1. Configure persistence layer (uses .env file automatically)
    config = PersistenceConfig(
        echo_sql=True,  # Enable SQL logging for development
    )

    # 2. Initialize persistence layer
    initializer = await initialize_persistence(config)

    try:
        # 3. Use repositories
        user_repo = await repository_registry.get_user_repository()

        # Create a new user
        new_user = User.create(
            email="john.doe@example.com",
            username="johndoe",
            first_name="John",
            last_name="Doe",
            role=UserRole.TRADER,
            preferred_currency=Currency.USD,
        )

        # Save user
        saved_user = await user_repo.save(new_user)
        logger.info(f"Created user: {saved_user.id}")

        # Find user by email
        found_user = await user_repo.find_by_email("john.doe@example.com")
        if found_user:
            logger.info(f"Found user: {found_user.full_name}")

        # Update user
        found_user.update_profile(first_name="Johnny")
        updated_user = await user_repo.save(found_user)
        logger.info(f"Updated user: {updated_user.first_name}")

    finally:
        # 4. Shutdown persistence layer
        await shutdown_persistence()


async def example_unit_of_work():
    """Example of using Unit of Work pattern for transactions."""

    # Use the same configuration as the first example
    config = PersistenceConfig(
        echo_sql=False,
    )

    initializer = await initialize_persistence(config)

    try:
        # Get Unit of Work
        uow = await repository_registry.get_unit_of_work()

        # Use AutoTransaction for automatic transaction management
        async with AutoTransaction(uow) as tx:
            # Create multiple users in a single transaction
            users = [
                User.create(
                    email=f"user{i}@example.com",
                    username=f"user{i}",
                    first_name="User",
                    last_name=f"{i}",
                    role=UserRole.VIEWER,
                )
                for i in range(5)
            ]

            # Save all users
            for user in users:
                await tx.users.save(user)
                logger.info(f"Saved user: {user.email}")

            # If any operation fails, all changes will be rolled back
            # If all operations succeed, changes will be committed automatically

        logger.info("Transaction completed successfully")

    except Exception as e:
        logger.error(f"Transaction failed: {e}")
    finally:
        await shutdown_persistence()


async def main():
    """Run all examples."""
    logger.info("Running persistence layer examples...")

    try:
        await example_basic_usage()
        logger.info("✓ Basic usage example completed")

        await example_unit_of_work()
        logger.info("✓ Unit of Work example completed")

    except Exception as e:
        logger.error(f"Example failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from src.domain.entities.user import User, UserRole
from src.domain.value_objects.money import Currency, Money
from src.infrastructure.persistence import (
    PersistenceLayerConfig,
    create_persistence_context,
    get_market_data_repository,
    get_portfolio_repository,
    get_uow,
    get_user_repository,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_basic_usage():
    """Example of basic persistence layer usage."""

    # Configuration
    database_url = (
        "postgresql+asyncpg://trading_user:password@localhost:5432/trading_platform"
    )

    config = PersistenceLayerConfig(
        database_url=database_url,
        pool_size=10,
        max_overflow=5,
        echo=False,  # Set to True for SQL debugging
        create_hypertables=True,
        create_indexes=True,
        setup_compression=True,
    )

    # Use persistence context for automatic setup/teardown
    async with create_persistence_context(database_url) as _:
        logger.info("Persistence layer initialized successfully")

        # Example 1: User operations
        await example_user_operations()

        # Example 2: Portfolio operations
        await example_portfolio_operations()

        # Example 3: Market data operations
        await example_market_data_operations()

        # Example 4: Unit of Work pattern
        await example_unit_of_work()

    logger.info("Persistence layer shutdown completed")


async def example_user_operations():
    """Example user repository operations."""
    logger.info("=== User Operations Example ===")

    user_repo = get_user_repository()

    # Create a new user
    user = User.create(
        email="john.doe@example.com",
        username="johndoe",
        first_name="John",
        last_name="Doe",
        role=UserRole.TRADER,
        preferred_currency=Currency.USD,
    )

    # Save user
    saved_user = await user_repo.save(user)
    logger.info(f"Created user: {saved_user.email}")

    # Find user by email
    found_user = await user_repo.find_by_email("john.doe@example.com")
    if found_user:
        logger.info(f"Found user: {found_user.full_name}")

    # Update user
    found_user.update_profile(first_name="Jonathan")
    updated_user = await user_repo.save(found_user)
    logger.info(f"Updated user: {updated_user.full_name}")


async def example_portfolio_operations():
    """Example portfolio repository operations."""
    logger.info("=== Portfolio Operations Example ===")

    portfolio_repo = get_portfolio_repository()
    user_repo = get_user_repository()

    # Get or create a user
    user = await user_repo.find_by_email("john.doe@example.com")
    if not user:
        user = User.create(
            email="john.doe@example.com",
            username="johndoe",
            first_name="John",
            last_name="Doe",
        )
        user = await user_repo.save(user)

    # Create portfolio
    from src.domain.entities.portfolio import Portfolio

    portfolio = Portfolio.create(
        user_id=user.id,
        name="My Trading Portfolio",
        base_currency=Currency.USD,
        initial_cash=Money(Decimal("10000.00"), Currency.USD),
    )

    # Save portfolio
    saved_portfolio = await portfolio_repo.save(portfolio)
    logger.info(f"Created portfolio: {saved_portfolio.name}")

    # Find portfolios by user
    user_portfolios = await portfolio_repo.find_by_user_id(user.id)
    logger.info(f"User has {len(user_portfolios)} portfolios")


async def example_market_data_operations():
    """Example market data repository operations."""
    logger.info("=== Market Data Operations Example ===")

    market_repo = get_market_data_repository()

    # Create sample market data
    from src.domain.entities.market_data import MarketData
    from src.domain.value_objects.price import Price

    market_data = MarketData.create(
        symbol="AAPL",
        timestamp=datetime.now(timezone.utc),
        prices={
            "open": Price(Decimal("150.00"), Currency.USD),
            "high": Price(Decimal("152.00"), Currency.USD),
            "low": Price(Decimal("149.00"), Currency.USD),
            "close": Price(Decimal("151.50"), Currency.USD),
            "adjusted_close": Price(Decimal("151.50"), Currency.USD),
        },
        volume=1000000,
        source="test",
    )

    # Save market data
    saved_data = await market_repo.save(market_data)
    logger.info(f"Saved market data for {saved_data.symbol}")

    # Find latest prices
    symbols = ["AAPL", "GOOGL", "MSFT"]
    latest_prices = await market_repo.find_latest_prices(symbols)
    logger.info(f"Found latest prices for {len(latest_prices)} symbols")

    # Get market summary
    summary = await market_repo.get_market_summary(["AAPL"])
    logger.info(f"Market summary: {summary}")


async def example_unit_of_work():
    """Example Unit of Work pattern usage."""
    logger.info("=== Unit of Work Example ===")

    # Use Unit of Work for transactional operations
    async with get_uow() as uow:
        # Create user and portfolio in same transaction
        user = User.create(
            email="jane.smith@example.com",
            username="janesmith",
            first_name="Jane",
            last_name="Smith",
            role=UserRole.ANALYST,
        )

        saved_user = await uow.users.save(user)
        logger.info(f"Created user in transaction: {saved_user.email}")

        # Create portfolio for the user
        from src.domain.entities.portfolio import Portfolio

        portfolio = Portfolio.create(
            user_id=saved_user.id,
            name="Jane's Analysis Portfolio",
            base_currency=Currency.USD,
            initial_cash=Money(Decimal("5000.00"), Currency.USD),
        )

        saved_portfolio = await uow.portfolios.save(portfolio)
        logger.info(f"Created portfolio in transaction: {saved_portfolio.name}")

        # Transaction is automatically committed when exiting the context


async def example_error_handling():
    """Example error handling and rollback."""
    logger.info("=== Error Handling Example ===")

    database_url = (
        "postgresql+asyncpg://trading_user:password@localhost:5432/trading_platform"
    )

    try:
        async with create_persistence_context(database_url):
            async with get_uow() as uow:
                # Create a user
                user = User.create(
                    email="test@example.com",
                    username="test",
                    first_name="Test",
                    last_name="User",
                )

                await uow.users.save(user)
                logger.info("User created successfully")

                # Simulate an error
                raise ValueError("Simulated error - transaction will be rolled back")

    except ValueError as e:
        logger.info(f"Caught expected error: {e}")
        logger.info("Transaction was automatically rolled back")


async def example_performance_monitoring():
    """Example of performance monitoring."""
    logger.info("=== Performance Monitoring Example ===")

    import time

    database_url = (
        "postgresql+asyncpg://trading_user:password@localhost:5432/trading_platform"
    )

    async with create_persistence_context(database_url):
        market_repo = get_market_data_repository()

        # Measure query performance
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]

        start_time = time.perf_counter()
        latest_prices = await market_repo.find_latest_prices(symbols)
        end_time = time.perf_counter()

        latency_ms = (end_time - start_time) * 1000
        logger.info(f"Latest prices query took {latency_ms:.2f}ms")
        logger.info(f"Found prices for {len(latest_prices)} symbols")

        # Check if we meet acceptance criteria (p95 < 100ms)
        if latency_ms < 100:
            logger.info("✅ Query performance meets acceptance criteria")
        else:
            logger.warning("❌ Query performance exceeds 100ms threshold")


if __name__ == "__main__":
    # Run examples
    async def main():
        await example_basic_usage()
        await example_error_handling()
        await example_performance_monitoring()

    asyncio.run(main())
