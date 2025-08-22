"""
Investment Repository Interface
==============================

Domain repository interface for investment operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from ..entities.investment import Investment


class IInvestmentRepository(ABC):
    """Repository interface for investment operations."""

    @abstractmethod
    async def find_by_symbol(self, symbol: str) -> Optional[Investment]:
        """Find investment by symbol."""
        pass

    @abstractmethod
    async def find_by_id(self, investment_id: str) -> Optional[Investment]:
        """Find investment by ID."""
        pass

    @abstractmethod
    async def find_by_exchange(self, exchange: str) -> List[Investment]:
        """Find investments by exchange."""
        pass

    @abstractmethod
    async def find_by_sector(self, sector: str) -> List[Investment]:
        """Find investments by sector."""
        pass

    @abstractmethod
    async def save(self, investment: Investment) -> Investment:
        """Save investment."""
        pass

    @abstractmethod
    async def find_all_active(self) -> List[Investment]:
        """Find all active investments."""
        pass

    @abstractmethod
    async def delete(self, investment: Investment) -> bool:
        """Delete investment.
        
        Returns:
            bool: True if deletion was successful, False if not found
        """
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Investment]:
        """Find all investments (alias for find_all_active).""" 
        pass
        
    @abstractmethod
    async def find_by_market_cap(self, market_cap: str) -> List[Investment]:
        """Find investments by market cap."""
        pass
        
    @abstractmethod
    async def search_by_name(self, name_pattern: str) -> List[Investment]:
        """Search investments by name pattern."""
        pass
