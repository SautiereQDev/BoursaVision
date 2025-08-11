"""
Temporary market data repository with all required methods.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.domain.entities.market_data import DataSource
from src.domain.entities.market_data import MarketData as DomainMarketData
from src.domain.entities.market_data import Timeframe
from src.domain.repositories.market_data_repository import IMarketDataRepository


class TempMarketDataRepository(IMarketDataRepository):
    """Temporary implementation with basic functionality."""

    async def save(self, entity: DomainMarketData) -> DomainMarketData:
        """Save market data."""
        return entity

    async def find_by_id(self, market_data_id: UUID) -> Optional[DomainMarketData]:
        """Find by ID."""
        return None

    async def delete(self, entity: DomainMarketData) -> None:
        """Delete entity."""
        pass

    async def find_by_symbol_and_timestamp(
        self, symbol: str, timestamp: datetime, timeframe: Timeframe = Timeframe.DAY_1
    ) -> Optional[DomainMarketData]:
        """Find market data by symbol and timestamp"""
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
        """Find market data for symbol within date range"""
        return []

    async def find_latest_by_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> Optional[DomainMarketData]:
        """Find latest market data for symbol"""
        return None

    async def find_latest_by_symbols(
        self, symbols: List[str], timeframe: Timeframe = Timeframe.DAY_1
    ) -> List[DomainMarketData]:
        """Find latest market data for multiple symbols"""
        return []

    async def delete_by_symbol_and_date_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> int:
        """Delete market data for symbol within date range"""
        return 0

    async def get_available_symbols(self) -> List[str]:
        """Get list of all available symbols"""
        return []

    async def get_date_range_for_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> Optional[tuple[datetime, datetime]]:
        """Get earliest and latest dates for symbol"""
        return None

    async def count_by_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> int:
        """Count market data points for symbol"""
        return 0

    async def exists_by_symbol_and_timestamp(
        self, symbol: str, timestamp: datetime, timeframe: Timeframe = Timeframe.DAY_1
    ) -> bool:
        """Check if market data exists for symbol and timestamp"""
        return False

    async def find_missing_dates(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> List[datetime]:
        """Find missing dates in market data for symbol"""
        return []

    async def cleanup_old_data(
        self, older_than_days: int, timeframe: Timeframe = Timeframe.MINUTE_1
    ) -> int:
        """Cleanup old market data (useful for minute data)"""
        return 0

    async def find_latest_prices(self, symbols: List[str]) -> List[DomainMarketData]:
        """Find latest prices for multiple symbols."""
        return []

    async def find_by_symbol_and_timerange(
        self, symbol: str, start_time: datetime, end_time: datetime
    ) -> List[DomainMarketData]:
        """Find market data by symbol and time range."""
        return []
