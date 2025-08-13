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
