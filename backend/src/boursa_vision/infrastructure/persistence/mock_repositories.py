"""
Simple mock repositories for testing purposes.
"""

from datetime import datetime
from uuid import UUID

from boursa_vision.domain.entities.market_data import DataSource, Timeframe
from boursa_vision.domain.entities.market_data import MarketData as DomainMarketData
from boursa_vision.domain.entities.portfolio import Portfolio as DomainPortfolio
from boursa_vision.domain.entities.user import User as DomainUser
from boursa_vision.domain.repositories.market_data_repository import (
    IMarketDataRepository,
)
from boursa_vision.domain.repositories.portfolio_repository import IPortfolioRepository
from boursa_vision.domain.repositories.user_repository import IUserRepository


class MockUserRepository(IUserRepository):
    """Mock implementation for testing."""

    async def find_by_id(self, entity_id: UUID) -> DomainUser | None:
        """Find a user by their ID."""
        return None

    async def save(self, entity: DomainUser) -> DomainUser:
        """Save a user entity."""
        return entity

    async def update(self, entity: DomainUser) -> DomainUser:
        """Update existing entity"""
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        """Delete entity by ID"""
        return True

    async def find_by_email(self, email: str) -> DomainUser | None:
        """Find a user by email."""
        return None

    async def find_by_email_for_auth(self, email: str) -> DomainUser | None:
        """Find a user by email for authentication."""
        return None

    async def find_by_username_for_auth(self, username: str) -> DomainUser | None:
        """Find a user by username for authentication."""
        return None

    async def find_by_username(self, username: str) -> DomainUser | None:
        """Find a user by username."""
        return None

    async def find_by_role(self, role: str) -> list[DomainUser]:
        """Find users by role."""
        return []

    async def find_active_users(self) -> list[DomainUser]:
        """Find all active users."""
        return []

    async def exists_by_email(self, email: str) -> bool:
        """Check if a user exists by email."""
        return False

    async def exists_by_username(self, username: str) -> bool:
        """Check if a user exists by username."""
        return False

    async def find_all(self, limit: int = 100, offset: int = 0) -> list[DomainUser]:
        """Find all users with pagination."""
        return []

    async def count_by_role(self, role: str) -> int:
        """Count users by role."""
        return 0


class MockPortfolioRepository(IPortfolioRepository):
    """Mock implementation for testing."""

    async def find_by_id(self, entity_id: UUID) -> DomainPortfolio | None:
        """Find a portfolio by ID."""
        return None

    async def save(self, entity: DomainPortfolio) -> DomainPortfolio:
        """Save a portfolio entity."""
        return entity

    async def update(self, entity: DomainPortfolio) -> DomainPortfolio:
        """Update existing entity"""
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a portfolio by ID."""
        return True

    async def find_by_user_id(self, user_id: UUID) -> list[DomainPortfolio]:
        """Find portfolios by user ID."""
        return []

    async def find_by_name(self, user_id: UUID, name: str) -> DomainPortfolio | None:
        """Find a portfolio by user ID and name."""
        return None

    async def exists(self, portfolio_id: UUID) -> bool:
        """Check if a portfolio exists by ID."""
        return False

    async def exists_by_name(self, user_id: UUID, name: str) -> bool:
        """Check if a portfolio exists by user ID and name."""
        return False

    async def count_by_user(self, user_id: UUID) -> int:
        """Count portfolios by user ID."""
        return 0

    async def find_all(
        self, limit: int = 100, offset: int = 0
    ) -> list[DomainPortfolio]:
        """Find all portfolios with pagination."""
        return []


class MockMarketDataRepository(IMarketDataRepository):
    """Mock implementation for testing."""

    async def find_by_id(self, entity_id: UUID) -> DomainMarketData | None:
        """Find market data by ID."""
        return None

    async def save(self, entity: DomainMarketData) -> DomainMarketData:
        """Save market data."""
        return entity

    async def update(self, entity: DomainMarketData) -> DomainMarketData:
        """Update existing entity"""
        return entity

    async def delete(self, entity_id: UUID) -> bool:
        """Delete market data by ID."""
        return True

    async def find_by_symbol_and_timestamp(
        self, symbol: str, timestamp: datetime, timeframe: Timeframe = Timeframe.DAY_1
    ) -> DomainMarketData | None:
        """Find market data by symbol and timestamp."""
        return None

    async def find_by_symbol(
        self,
        symbol: str,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        timeframe: Timeframe = Timeframe.DAY_1,
        source: DataSource | None = None,
        limit: int = 1000,
    ) -> list[DomainMarketData]:
        """Find market data by symbol with optional date range, timeframe, and source."""
        return []

    async def find_latest_by_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> DomainMarketData | None:
        """Find the latest market data by symbol."""
        return None

    async def find_latest_by_symbols(
        self, symbols: list[str], timeframe: Timeframe = Timeframe.DAY_1
    ) -> list[DomainMarketData]:
        """Find the latest market data for multiple symbols."""
        return []

    async def delete_by_symbol_and_date_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> int:
        """Delete market data by symbol and date range."""
        return 0

    async def get_available_symbols(self) -> list[str]:
        """Get a list of available symbols."""
        return []

    async def get_date_range_for_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> tuple[datetime, datetime] | None:
        """Get the date range for a given symbol."""
        return None

    async def count_by_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> int:
        """Count market data entries by symbol."""
        return 0

    async def exists_by_symbol_and_timestamp(
        self, symbol: str, timestamp: datetime, timeframe: Timeframe = Timeframe.DAY_1
    ) -> bool:
        """Check if market data exists by symbol and timestamp."""
        return False

    async def find_missing_dates(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> list[datetime]:
        """Find missing dates for a given symbol and date range."""
        return []

    async def cleanup_old_data(
        self, older_than_days: int, timeframe: Timeframe = Timeframe.MINUTE_1
    ) -> int:
        """Clean up old market data."""
        return 0

    async def find_latest_prices(self, symbols: list[str]) -> list[DomainMarketData]:
        """Find the latest prices for a list of symbols."""
        return []

    async def find_by_symbol_and_timerange(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> list[DomainMarketData]:
        """Find market data by symbol and time range."""
        return []
