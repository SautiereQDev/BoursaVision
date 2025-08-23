"""
Base Repository Interface
========================

Defines common repository methods for all aggregates.

Classes:
    IBaseRepository: Abstract base interface for persistence operations.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

T = TypeVar("T")


class IBaseRepository(ABC, Generic[T]):
    """
    Abstract base repository interface.

    Provides common persistence operations for all aggregates.
    """

    @abstractmethod
    async def find_by_id(self, entity_id: UUID) -> T | None:
        """Find entity by ID"""
        raise NotImplementedError

    @abstractmethod
    async def save(self, entity: T) -> T:
        """Save entity (create or update)"""
        raise NotImplementedError

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update existing entity"""
        raise NotImplementedError

    @abstractmethod
    async def delete(self, entity_id: UUID) -> bool:
        """Delete entity by ID"""
        raise NotImplementedError
