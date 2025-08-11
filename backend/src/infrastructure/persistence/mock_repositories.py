"""
Simple mock repositories for testing purposes.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.domain.entities.market_data import DataSource
from src.domain.entities.market_data import MarketData as DomainMarketData
from src.domain.entities.market_data import Timeframe
from src.domain.entities.portfolio import Portfolio as DomainPortfolio
from src.domain.entities.user import User as DomainUser
from src.domain.repositories.market_data_repository import IMarketDataRepository
from src.domain.repositories.portfolio_repository import IPortfolioRepository
from src.domain.repositories.user_repository import IUserRepository


class MockUserRepository(IUserRepository):
    """Mock implementation for testing."""

    async def save(self, entity: DomainUser) -> DomainUser:
        return entity

    async def find_by_id(self, user_id: UUID) -> Optional[DomainUser]:
        return None

    async def delete(self, entity: DomainUser) -> None:
        # Mock implementation - no actual deletion
        pass

    async def find_by_email(self, email: str) -> Optional[DomainUser]:
        return None

    async def find_by_username(self, username: str) -> Optional[DomainUser]:
        return None

    async def exists_by_email(self, email: str) -> bool:
        return False

    async def exists_by_username(self, username: str) -> bool:
        return False

    async def find_all(self, limit: int = 100, offset: int = 0) -> List[DomainUser]:
        return []

    async def find_by_role(self, role: str) -> List[DomainUser]:
        return []

    async def find_active_users(self) -> List[DomainUser]:
        return []

    async def count_by_role(self, role: str) -> int:
        return 0


class MockPortfolioRepository(IPortfolioRepository):
    """Mock implementation for testing."""

    async def save(self, entity: DomainPortfolio) -> DomainPortfolio:
        return entity

    async def find_by_id(self, portfolio_id: UUID) -> Optional[DomainPortfolio]:
        return None

    async def delete(self, portfolio_id: UUID) -> bool:
        return True

    async def find_by_user_id(self, user_id: UUID) -> List[DomainPortfolio]:
        return []

    async def find_by_name(self, user_id: UUID, name: str) -> Optional[DomainPortfolio]:
        return None

    async def exists(self, portfolio_id: UUID) -> bool:
        return False

    async def exists_by_name(self, user_id: UUID, name: str) -> bool:
        return False

    async def count_by_user(self, user_id: UUID) -> int:
        return 0

    async def find_all(self, limit: int = 100, offset: int = 0) -> List[DomainPortfolio]:
        return []


class MockMarketDataRepository(IMarketDataRepository):
    """Mock implementation for testing."""

    async def save(self, entity: DomainMarketData) -> DomainMarketData:
        return entity

    async def find_by_id(self, market_data_id: UUID) -> Optional[DomainMarketData]:
        return None

    async def delete(self, entity: DomainMarketData) -> None:
        # Mock implementation - no actual deletion
        pass

    async def find_by_symbol_and_timestamp(
        self, symbol: str, timestamp: datetime, timeframe: Timeframe = Timeframe.DAY_1
    ) -> Optional[DomainMarketData]:
        return None

    async def find_by_symbol(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: Timeframe = Timeframe.DAY_1,
        source: Optional[DataSource] = None,
        limit: int = 1000,
    ) -> List[DomainMarketData]:
        return []

    async def find_latest_by_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> Optional[DomainMarketData]:
        return None

    async def find_latest_by_symbols(
        self, symbols: List[str], timeframe: Timeframe = Timeframe.DAY_1
    ) -> List[DomainMarketData]:
        return []

    async def delete_by_symbol_and_date_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> int:
        return 0

    async def get_available_symbols(self) -> List[str]:
        return []

    async def get_date_range_for_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> Optional[tuple[datetime, datetime]]:
        return None

    async def count_by_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> int:
        return 0

    async def exists_by_symbol_and_timestamp(
        self, symbol: str, timestamp: datetime, timeframe: Timeframe = Timeframe.DAY_1
    ) -> bool:
        return False

    async def find_missing_dates(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> List[datetime]:
        return []

    async def cleanup_old_data(
        self, older_than_days: int, timeframe: Timeframe = Timeframe.MINUTE_1
    ) -> int:
        return 0

    async def find_latest_prices(self, symbols: List[str]) -> List[DomainMarketData]:
        return []

    async def find_by_symbol_and_timerange(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[DomainMarketData]:
        return []
