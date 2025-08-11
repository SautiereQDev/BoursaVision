"""
Temporary user repository with all required methods.
"""

from typing import Dict, List, Optional
from uuid import UUID

from src.domain.entities.user import User as DomainUser
from src.domain.repositories.user_repository import IUserRepository


class TempUserRepository(IUserRepository):
    """Temporary implementation with basic functionality."""

    def __init__(self):
        # Simple in-memory storage for testing
        self._users: Dict[str, DomainUser] = {}
        self._users_by_id: Dict[UUID, DomainUser] = {}

    async def save(self, entity: DomainUser) -> DomainUser:
        """Save user."""
        self._users[entity.email] = entity
        if entity.username:
            self._users[entity.username] = entity
        self._users_by_id[entity.id] = entity
        return entity

    async def find_by_id(self, user_id: UUID) -> Optional[DomainUser]:
        """Find by ID."""
        return self._users_by_id.get(user_id)

    async def delete(self, entity: DomainUser) -> None:
        """Delete entity."""
        if entity.email in self._users:
            del self._users[entity.email]
        if entity.username and entity.username in self._users:
            del self._users[entity.username]
        if entity.id in self._users_by_id:
            del self._users_by_id[entity.id]

    async def find_by_email(self, email: str) -> Optional[DomainUser]:
        """Find user by email."""
        return self._users.get(email)

    async def find_by_username(self, username: str) -> Optional[DomainUser]:
        """Find user by username."""
        return self._users.get(username)

    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email."""
        return email in self._users

    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists by username."""
        return username in self._users

    async def count_by_role(self, role: str) -> int:
        """Count users by role."""
        return len([u for u in self._users_by_id.values() if u.role == role])

    async def find_active_users(
        self, limit: int = 100, offset: int = 0
    ) -> List[DomainUser]:
        """Find active users."""
        users = list(self._users_by_id.values())
        return users[offset : offset + limit]

    async def find_all(self, limit: int = 100, offset: int = 0) -> List[DomainUser]:
        """Find all users."""
        users = list(self._users_by_id.values())
        return users[offset : offset + limit]

    async def find_by_role(
        self, role: str, limit: int = 100, offset: int = 0
    ) -> List[DomainUser]:
        """Find users by role."""
        users = [u for u in self._users_by_id.values() if u.role == role]
        return users[offset : offset + limit]
