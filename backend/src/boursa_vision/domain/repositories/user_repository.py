"""
User Repository Interface
========================

Repository interface for user aggregate following DDD patterns.

Classes:
    IUserRepository: Abstract interface for user persistence operations.
"""

from abc import ABC, abstractmethod

from ..entities.user import User, UserRole
from .base_repository import IBaseRepository


class IUserRepository(IBaseRepository[User], ABC):
    """
    Repository interface for User aggregate.

    Defines the contract for user persistence operations
    without coupling to specific infrastructure.
    """

    @abstractmethod
    async def find_by_email(self, email: str) -> User | None:
        """Find user by email address"""
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None:
        """Find user by username"""
        pass

    @abstractmethod
    async def find_by_role(self, role: UserRole) -> list[User]:
        """Find all users with specific role"""
        pass

    @abstractmethod
    async def find_active_users(self) -> list[User]:
        """Find all active users"""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user with email exists"""
        pass

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if user with username exists"""
        pass

    @abstractmethod
    async def count_by_role(self, role: UserRole) -> int:
        """Count users by role"""
        pass

    @abstractmethod
    async def find_all(
        self, offset: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> list[User]:
        """Find all users with pagination"""
        pass
