"""
SQLAlchemy repository implementations for User entity.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from src.domain.entities.user import User as DomainUser
from src.domain.entities.user import UserRole
from src.domain.repositories.user_repository import IUserRepository
from src.infrastructure.persistence.mappers_new import UserMapper
from src.infrastructure.persistence.models.users import User


class SQLAlchemyUserRepository(IUserRepository):
    """SQLAlchemy implementation of user repository."""

    def __init__(self, session: AsyncSession):
        self._session = session
        self._mapper = UserMapper()

    async def find_by_id(self, user_id: UUID) -> Optional[DomainUser]:
        """Find user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self._session.execute(query)
        user_model = result.scalar_one_or_none()

        if user_model is None:
            return None

        return self._mapper.to_domain(user_model)

    async def find_by_email(self, email: str) -> Optional[DomainUser]:
        """Find user by email."""
        query = select(User).where(User.email == email)
        result = await self._session.execute(query)
        user_model = result.scalar_one_or_none()

        if user_model is None:
            return None

        return self._mapper.to_domain(user_model)

    async def find_by_username(self, username: str) -> Optional[DomainUser]:
        """Find user by username."""
        query = select(User).where(User.username == username)
        result = await self._session.execute(query)
        user_model = result.scalar_one_or_none()

        if user_model is None:
            return None

        return self._mapper.to_domain(user_model)

    async def find_by_role(self, role: UserRole) -> List[DomainUser]:
        """Find all users with specific role."""
        query = select(User).where(User.role == role.value)
        result = await self._session.execute(query)
        user_models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in user_models]

    async def find_active_users(self) -> List[DomainUser]:
        """Find all active users."""
        query = select(User).where(User.is_active.is_(True))
        result = await self._session.execute(query)
        user_models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in user_models]

    async def exists_by_email(self, email: str) -> bool:
        """Check if user with email exists."""
        query = select(func.count(User.id)).where(User.email == email)
        result = await self._session.execute(query)
        count = result.scalar()
        return count > 0

    async def exists_by_username(self, username: str) -> bool:
        """Check if user with username exists."""
        query = select(func.count(User.id)).where(User.username == username)
        result = await self._session.execute(query)
        count = result.scalar()
        return count > 0

    async def count_by_role(self, role: UserRole) -> int:
        """Count users by role."""
        query = select(func.count(User.id)).where(User.role == role.value)
        result = await self._session.execute(query)
        return result.scalar()

    async def find_all(
        self, offset: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> List[DomainUser]:
        """Find all users with pagination."""
        query = select(User)

        if not include_inactive:
            query = query.where(User.is_active.is_(True))

        query = query.offset(offset).limit(limit)
        result = await self._session.execute(query)
        user_models = result.scalars().all()

        return [self._mapper.to_domain(model) for model in user_models]

    async def save(self, user: DomainUser) -> DomainUser:
        """Save user."""
        user_model = self._mapper.to_persistence(user)

        # Check if user exists
        existing = await self._session.get(User, user.id)

        if existing:
            # Update existing
            for key, value in user_model.__dict__.items():
                if not key.startswith("_") and key != "id":
                    setattr(existing, key, value)
            user_model = existing
        else:
            # Create new
            self._session.add(user_model)

        await self._session.flush()
        await self._session.refresh(user_model)

        return self._mapper.to_domain(user_model)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete a user by their ID."""
        user_model = await self._session.get(User, entity_id)

        if user_model is None:
            return False

        await self._session.delete(user_model)
        await self._session.flush()

        return True
