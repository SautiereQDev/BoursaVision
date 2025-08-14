"""
Market Data Repository Interface
===============================

Repository interface for market data aggregate following DDD patterns.

Classes:
    IMarketDataRepository: Abstract interface for market data persistence operations.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ..entities.market_data import DataSource, MarketData, Timeframe
from .base_repository import IBaseRepository


class IMarketDataRepository(IBaseRepository[MarketData], ABC):
    """
    Repository interface for MarketData aggregate.

    Defines the contract for market data persistence operations
    without coupling to specific infrastructure.
    """

    @abstractmethod
    async def find_by_symbol_and_timestamp(
        self, symbol: str, timestamp: datetime, timeframe: Timeframe = Timeframe.DAY_1
    ) -> Optional[MarketData]:
        """Find market data by symbol and timestamp"""
        pass

    @abstractmethod
    async def find_by_symbol(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        timeframe: Timeframe = Timeframe.DAY_1,
        source: Optional[DataSource] = None,
        limit: int = 1000,
    ) -> List[MarketData]:
        """Find market data for symbol within date range"""
        pass

    @abstractmethod
    async def find_latest_by_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> Optional[MarketData]:
        """Find latest market data for symbol"""
        pass

    @abstractmethod
    async def find_latest_by_symbols(
        self, symbols: List[str], timeframe: Timeframe = Timeframe.DAY_1
    ) -> List[MarketData]:
        """Find latest market data for multiple symbols"""
        pass

    @abstractmethod
    async def delete_by_symbol_and_date_range(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> int:
        """Delete market data for symbol within date range"""
        pass

    @abstractmethod
    async def get_available_symbols(self) -> List[str]:
        """Get list of all available symbols"""
        pass

    @abstractmethod
    async def get_date_range_for_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> Optional[tuple[datetime, datetime]]:
        """Get earliest and latest dates for symbol"""
        pass

    @abstractmethod
    async def count_by_symbol(
        self, symbol: str, timeframe: Timeframe = Timeframe.DAY_1
    ) -> int:
        """Count market data points for symbol"""
        pass

    @abstractmethod
    async def exists_by_symbol_and_timestamp(
        self, symbol: str, timestamp: datetime, timeframe: Timeframe = Timeframe.DAY_1
    ) -> bool:
        """Check if market data exists for symbol and timestamp"""
        pass

    @abstractmethod
    async def find_missing_dates(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        timeframe: Timeframe = Timeframe.DAY_1,
    ) -> List[datetime]:
        """Find missing dates in market data for symbol"""
        pass

    @abstractmethod
    async def cleanup_old_data(
        self, older_than_days: int, timeframe: Timeframe = Timeframe.MINUTE_1
    ) -> int:
        """Cleanup old market data (useful for minute data)"""
        pass
