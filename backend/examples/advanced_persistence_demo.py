"""
Advanced Persistence Layer Usage Example
=======================================

This example demonstrates advanced usage of the persistence layer including:
- Unit of Work pattern for transactions
- Repository pattern for data access
- TimescaleDB hypertables for time-series data
- Performance monitoring and optimization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List

from src.domain.entities.market_data import DataSource, MarketData, Timeframe
from src.domain.entities.portfolio import Portfolio
from src.domain.entities.user import User, UserRole
from src.domain.value_objects.money import Currency, Money
from src.domain.value_objects.price import Price
from src.infrastructure.persistence import (
    create_persistence_context,
    get_market_data_repository,
    get_portfolio_repository,
    get_user_repository,
    quick_setup,
)
from src.infrastructure.persistence.unit_of_work import get_uow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demonstrate_basic_repository_usage():
    """Demonstrate basic repository operations."""
    logger.info("=== Basic Repository Usage ===")
    
    # Get repositories
    user_repo = get_user_repository()
    portfolio_repo = get_portfolio_repository()
    market_data_repo = get_market_data_repository()
    
    # Create a test user
    user = User.create(
        email="test@example.com",
        username="testuser",
        password_hash="hashed_password",
        role=UserRole.TRADER
    )
    
    # Save user
    saved_user = await user_repo.save(user)
    logger.info(f"Created user: {saved_user.username}")
    
    # Create a portfolio for the user
    portfolio = Portfolio.create(
        user_id=saved_user.id,
        name="My Test Portfolio",
        base_currency=Currency.USD,
        initial_cash=Money(Decimal("10000.00"), Currency.USD)
    )
    
    # Save portfolio
    saved_portfolio = await portfolio_repo.save(portfolio)
    logger.info(f"Created portfolio: {saved_portfolio.name}")
    
    # Create some market data
    market_data = MarketData.create(
        symbol="AAPL",
        timeframe=Timeframe.DAILY,
        timestamp=datetime.now(),
        open_price=Price(Decimal("150.00"), Currency.USD),
        high_price=Price(Decimal("155.00"), Currency.USD),
        low_price=Price(Decimal("149.00"), Currency.USD),
        close_price=Price(Decimal("154.00"), Currency.USD),
        volume=1000000,
        source=DataSource.YFINANCE
    )
    
    # Save market data
    saved_market_data = await market_data_repo.save(market_data)
    logger.info(f"Saved market data for {saved_market_data.symbol}")
    
    return saved_user, saved_portfolio, saved_market_data


async def demonstrate_unit_of_work_pattern():
    """Demonstrate Unit of Work pattern for transactional operations."""
    logger.info("=== Unit of Work Pattern ===")
    
    async with get_uow() as uow:
        # All operations within this block are part of the same transaction
        
        # Create multiple users
        users = []
        for i in range(3):
            user = User.create(
                email=f"trader{i}@example.com",
                username=f"trader{i}",
                password_hash="hashed_password",
                role=UserRole.TRADER
            )
            saved_user = await uow.users.save(user)
            users.append(saved_user)
            logger.info(f"Created user in transaction: {saved_user.username}")
        
        # Create portfolios for each user
        portfolios = []
        for user in users:
            portfolio = Portfolio.create(
                user_id=user.id,
                name=f"{user.username}'s Portfolio",
                base_currency=Currency.USD,
                initial_cash=Money(Decimal("5000.00"), Currency.USD)
            )
            saved_portfolio = await uow.portfolios.save(portfolio)
            portfolios.append(saved_portfolio)
            logger.info(f"Created portfolio in transaction: {portfolio.name}")
        
        # Add market data for multiple symbols
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        market_data_list = []
        
        for symbol in symbols:
            for days_back in range(30):  # 30 days of data
                timestamp = datetime.now() - timedelta(days=days_back)
                market_data = MarketData.create(
                    symbol=symbol,
                    timeframe=Timeframe.DAILY,
                    timestamp=timestamp,
                    open_price=Price(Decimal(f"{100 + days_back}.00"), Currency.USD),
                    high_price=Price(Decimal(f"{105 + days_back}.00"), Currency.USD),
                    low_price=Price(Decimal(f"{95 + days_back}.00"), Currency.USD),
                    close_price=Price(Decimal(f"{102 + days_back}.00"), Currency.USD),
                    volume=1000000 + (days_back * 10000),
                    source=DataSource.YFINANCE
                )
                saved_data = await uow.market_data.save(market_data)
                market_data_list.append(saved_data)
        
        logger.info(f"Created {len(market_data_list)} market data records in transaction")
        
        # Transaction will be committed automatically when exiting the context
        # If any error occurred, it would be rolled back automatically
    
    logger.info("Unit of Work transaction completed successfully")
    return users, portfolios, market_data_list


async def demonstrate_timescaledb_queries():
    """Demonstrate TimescaleDB time-series queries."""
    logger.info("=== TimescaleDB Queries ===")
    
    market_data_repo = get_market_data_repository()
    
    # Query latest prices for multiple symbols
    symbols = ["AAPL", "GOOGL", "MSFT"]
    latest_prices = await market_data_repo.get_latest_prices(symbols)
    logger.info(f"Latest prices for {len(symbols)} symbols:")
    for symbol, price in latest_prices.items():
        logger.info(f"  {symbol}: {price}")
    
    # Query historical data for a specific symbol
    symbol = "AAPL"
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    history = await market_data_repo.get_price_history(
        symbol=symbol,
        start_date=start_date,
        end_date=end_date,
        timeframe=Timeframe.DAILY
    )
    
    logger.info(f"Historical data for {symbol} (last 7 days): {len(history)} records")
    
    # Query by time range with limit
    recent_data = await market_data_repo.find_by_symbol_and_timerange(
        symbol=symbol,
        start_time=start_date,
        end_time=end_date,
        timeframe=Timeframe.DAILY,
        limit=5
    )
    
    logger.info(f"Recent data with limit: {len(recent_data)} records")
    
    return latest_prices, history, recent_data


async def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring capabilities."""
    logger.info("=== Performance Monitoring ===")
    
    # Measure repository operation performance
    start_time = datetime.now()
    
    # Perform a batch of operations
    market_data_repo = get_market_data_repository()
    
    # Batch save operation
    batch_data = []
    for i in range(100):
        market_data = MarketData.create(
            symbol=f"TEST{i:03d}",
            timeframe=Timeframe.DAILY,
            timestamp=datetime.now() - timedelta(minutes=i),
            open_price=Price(Decimal(f"{100 + i}.00"), Currency.USD),
            high_price=Price(Decimal(f"{105 + i}.00"), Currency.USD),
            low_price=Price(Decimal(f"{95 + i}.00"), Currency.USD),
            close_price=Price(Decimal(f"{102 + i}.00"), Currency.USD),
            volume=1000000 + (i * 1000),
            source=DataSource.YFINANCE
        )
        batch_data.append(market_data)
    
    # Save batch (if supported)
    try:
        await market_data_repo.save_batch(batch_data)
        logger.info(f"Batch saved {len(batch_data)} records")
    except AttributeError:
        # Fallback to individual saves if batch not supported
        for data in batch_data:
            await market_data_repo.save(data)
        logger.info(f"Individually saved {len(batch_data)} records")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"Performance test completed in {duration:.2f} seconds")
    logger.info(f"Throughput: {len(batch_data) / duration:.2f} records/second")
    
    # Check if we meet the acceptance criteria (P95 < 100ms)
    avg_latency_ms = (duration * 1000) / len(batch_data)
    logger.info(f"Average latency per operation: {avg_latency_ms:.2f}ms")
    
    if avg_latency_ms < 100:
        logger.info("✅ Performance meets acceptance criteria (< 100ms)")
    else:
        logger.warning("⚠️ Performance may need optimization")


async def cleanup_test_data():
    """Clean up test data."""
    logger.info("=== Cleanup ===")
    
    try:
        # Clean up old test data
        market_data_repo = get_market_data_repository()
        deleted_count = await market_data_repo.delete_old_data(days_to_keep=1)
        logger.info(f"Cleaned up {deleted_count} old market data records")
    except Exception as e:
        logger.warning(f"Cleanup failed: {e}")


async def main():
    """Main demonstration function."""
    logger.info("Starting Advanced Persistence Layer Demo")
    logger.info("=" * 50)
    
    try:
        # Initialize persistence layer
        await quick_setup()
        logger.info("Persistence layer initialized")
        
        # Run demonstrations
        await demonstrate_basic_repository_usage()
        await demonstrate_unit_of_work_pattern()
        await demonstrate_timescaledb_queries()
        await demonstrate_performance_monitoring()
        
        # Cleanup
        await cleanup_test_data()
        
        logger.info("=" * 50)
        logger.info("Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
