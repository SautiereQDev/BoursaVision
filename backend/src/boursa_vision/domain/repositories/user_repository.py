"""
User Repository Interface
========================

Repository interface for user aggregate following DDD patterns.

Classes:
    IUserRepository: Abstract interface for user persistence operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from ..entities.user import User, UserRole
from .base_repository import IBaseRepository


class IUserRepository(IBaseRepository[User], ABC):
    """
    Repository interface for User aggregate.

    Defines the contract for user persistence operations
    without coupling to specific infrastructure.
    """

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email address"""
        raise NotImplementedError

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        raise NotImplementedError

    @abstractmethod
    async def find_by_role(self, role: UserRole) -> List[User]:
        """Find all users with specific role"""
        raise NotImplementedError

    @abstractmethod
    async def find_active_users(self) -> List[User]:
        """Find all active users"""
        raise NotImplementedError

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user with email exists"""
        raise NotImplementedError

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if user with username exists"""
        raise NotImplementedError

    @abstractmethod
    async def count_by_role(self, role: UserRole) -> int:
        """Count users by role"""
        raise NotImplementedError

    @abstractmethod
    async def find_all(
        self, offset: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> List[User]:
        """Find all users with pagination"""
        raise NotImplementedError
    
    @abstractmethod
    async def find_by_email_for_auth(self, email: str) -> Optional[User]:
        """Find user by email for authentication (includes password hash)"""
        raise NotImplementedError
    
    @abstractmethod
    async def find_by_username_for_auth(self, username: str) -> Optional[User]:
        """Find user by username for authentication (includes password hash)"""
        raise NotImplementedError
