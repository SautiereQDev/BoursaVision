"""
Portfolio Repository Interface
=============================

Repository interface for portfolio aggregate following DDD patterns.

Classes:
    IPortfolioRepository: Abstract interface for portfolio persistence operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.portfolio import Portfolio


class IPortfolioRepository(ABC):
    """
    Repository interface for Portfolio aggregate.

    Defines the contract for portfolio persistence operations
    without coupling to specific infrastructure.
    """

    @abstractmethod
    async def find_by_id(self, portfolio_id: UUID) -> Optional[Portfolio]:
        """Find portfolio by ID"""
        pass

    @abstractmethod
    async def find_by_user_id(self, user_id: UUID) -> List[Portfolio]:
        """Find all portfolios for a user"""
        pass

    @abstractmethod
    async def find_by_name(self, user_id: UUID, name: str) -> Optional[Portfolio]:
        """Find portfolio by user and name"""
        pass

    @abstractmethod
    async def save(self, portfolio: Portfolio) -> Portfolio:
        """Save portfolio (create or update)"""
        pass

    @abstractmethod
    async def delete(self, portfolio_id: UUID) -> bool:
        """Delete portfolio by ID"""
        pass

    @abstractmethod
    async def exists(self, portfolio_id: UUID) -> bool:
        """Check if portfolio exists"""
        pass

    @abstractmethod
    async def exists_by_name(self, user_id: UUID, name: str) -> bool:
        """Check if portfolio with name exists for user"""
        pass

    @abstractmethod
    async def count_by_user(self, user_id: UUID) -> int:
        """Count portfolios for user"""
        pass

    @abstractmethod
    async def find_all(self, offset: int = 0, limit: int = 100) -> List[Portfolio]:
        """Find all portfolios with pagination"""
        pass
