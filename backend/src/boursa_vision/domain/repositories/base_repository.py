"""
Base Repository Interface
========================

Defines common repository methods for all aggregates.

Classes:
    IBaseRepository: Abstract base interface for persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar
from uuid import UUID

T = TypeVar("T")


class IBaseRepository(ABC, Generic[T]):
    """
    Abstract base repository interface.

    Provides common persistence operations for all aggregates.
    """

    @abstractmethod
    async def find_by_id(self, entity_id: UUID) -> Optional[T]:
        """Find entity by ID"""
        pass

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save entity (create or update)"""
        pass

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete entity by ID"""
        pass
