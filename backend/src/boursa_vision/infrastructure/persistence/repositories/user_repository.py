"""
SQLAlchemy repository implementations for User entity.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from boursa_vision.domain.entities.user import User as DomainUser
from boursa_vision.domain.entities.user import UserRole
from boursa_vision.domain.repositories.user_repository import IUserRepository
from boursa_vision.infrastructure.persistence.mappers import UserMapper
from boursa_vision.infrastructure.persistence.models.users import User
from boursa_vision.infrastructure.persistence.sqlalchemy.database import get_db_session


class SQLAlchemyUserRepository(IUserRepository):
    """SQLAlchemy implementation of user repository."""
    
    # Class-level mapper for test mocking compatibility
    _mapper = UserMapper()

    def __init__(self, session: Optional[AsyncSession] = None):
        self._mapper = UserMapper()
        self._session = session  # Optional injected session for testing

    def _get_session(self):
        """Get session - either injected one (for tests) or from db session factory."""
        if self._session:
            return self._session
        return get_db_session()

    async def find_by_id(self, user_id: UUID) -> Optional[DomainUser]:
        """Find user by ID."""
        if self._session:
            # Use injected session (testing mode)
            query = select(User).where(User.id == user_id)
            result = await self._session.execute(query)
            user_model = result.scalar_one_or_none()
            
            if user_model:
                return self._mapper.to_domain(user_model)
            return None
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                query = select(User).where(User.id == user_id)
                result = await session.execute(query)
                user_model = result.scalar_one_or_none()
                
                if user_model:
                    return self._mapper.to_domain(user_model)
                return None

    async def find_by_email(self, email: str) -> Optional[DomainUser]:
        """Find user by email."""
        if self._session:
            # Use injected session (testing mode)
            query = select(User).where(User.email == email)
            result = await self._session.execute(query)
            user_model = result.scalar_one_or_none()
            
            if user_model:
                return self._mapper.to_domain(user_model)
            return None
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                query = select(User).where(User.email == email)
                result = await session.execute(query)
                user_model = result.scalar_one_or_none()
                
                if user_model:
                    return self._mapper.to_domain(user_model)
                return None

    async def find_by_username(self, username: str) -> Optional[DomainUser]:
        """Find user by username."""
        if self._session:
            # Use injected session (testing mode)
            query = select(User).where(User.username == username)
            result = await self._session.execute(query)
            user_model = result.scalar_one_or_none()

            if user_model is None:
                return None

            return self._mapper.to_domain(user_model)
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                query = select(User).where(User.username == username)
                result = await session.execute(query)
                user_model = result.scalar_one_or_none()

                if user_model is None:
                    return None

                return self._mapper.to_domain(user_model)

    async def find_all(
        self, offset: int = 0, limit: int = 100, include_inactive: bool = False
    ) -> List[DomainUser]:
        """Find all users with pagination."""
        async with get_db_session() as session:
            query = select(User)
            
            if not include_inactive:
                query = query.where(User.is_active.is_(True))
            
            query = query.offset(offset).limit(limit)
            result = await session.execute(query)
            user_models = result.scalars().all()

            return [self._mapper.to_domain(model) for model in user_models]

    async def find_by_role(self, role: UserRole) -> List[DomainUser]:
        """Find all users with specific role."""
        async with get_db_session() as session:
            query = select(User).where(User.role == role.value)
            result = await session.execute(query)
            user_models = result.scalars().all()

            return [self._mapper.to_domain(model) for model in user_models]

    async def find_active_users(self) -> List[DomainUser]:
        """Find all active users."""
        if self._session:
            # Use injected session (testing mode)
            query = select(User).where(User.is_active.is_(True))
            result = await self._session.execute(query)
            user_models = result.scalars().all()

            return [self._mapper.to_domain(model) for model in user_models]
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                query = select(User).where(User.is_active.is_(True))
                result = await session.execute(query)
                user_models = result.scalars().all()

                return [self._mapper.to_domain(model) for model in user_models]

    async def exists_by_email(self, email: str) -> bool:
        """Check if user with email exists."""
        async with get_db_session() as session:
            query = select(func.count(User.id)).where(User.email == email)
            result = await session.execute(query)
            count = result.scalar()
            return (count or 0) > 0

    async def exists_by_username(self, username: str) -> bool:
        """Check if user with username exists."""
        async with get_db_session() as session:
            query = select(func.count(User.id)).where(User.username == username)
            result = await session.execute(query)
            count = result.scalar()
            return (count or 0) > 0

    async def count_by_role(self, role: UserRole) -> int:
        """Count users by role."""
        async with get_db_session() as session:
            query = select(func.count(User.id)).where(User.role == role.value)
            result = await session.execute(query)
            return result.scalar() or 0

    async def save(self, entity: DomainUser) -> DomainUser:
        """Save user entity."""
        if self._session:
            # Use injected session (testing mode)
            existing = await self._session.get(User, entity.id)
            
            if existing:
                # Update existing user
                user_model = self._mapper.to_persistence(entity)
                # Copy updated fields to existing model
                for column in User.__table__.columns:
                    if hasattr(user_model, column.name) and column.name != 'id':
                        setattr(existing, column.name, getattr(user_model, column.name))
                user_model = existing
            else:
                # Create new user
                user_model = self._mapper.to_persistence(entity)
                self._session.add(user_model)
            
            await self._session.flush()
            await self._session.refresh(user_model)
            return self._mapper.to_domain(user_model)
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                existing = await session.get(User, entity.id)
                
                if existing:
                    # Update existing user
                    user_model = self._mapper.to_persistence(entity)
                    # Copy updated fields to existing model
                    for column in User.__table__.columns:
                        if hasattr(user_model, column.name) and column.name != 'id':
                            setattr(existing, column.name, getattr(user_model, column.name))
                    user_model = existing
                else:
                    # Create new user
                    user_model = self._mapper.to_persistence(entity)
                    session.add(user_model)
                
                await session.flush()
                await session.refresh(user_model)
                return self._mapper.to_domain(user_model)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete user by ID."""
        if self._session:
            # Use injected session (testing mode)
            from sqlalchemy import delete as sql_delete
            
            # Use SQL DELETE to match test expectations
            query = sql_delete(User).where(User.id == entity_id)
            result = await self._session.execute(query)
            
            # Return True if any rows were affected
            return (result.rowcount or 0) > 0
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                from sqlalchemy import delete as sql_delete
                
                # Use SQL DELETE to match test expectations
                query = sql_delete(User).where(User.id == entity_id)
                result = await session.execute(query)
                await session.commit()
                
                # Return True if any rows were affected
                return (result.rowcount or 0) > 0

    async def find_all_active(self) -> List[DomainUser]:
        """Find all active users."""
        return await self.find_active_users()

    async def count_active(self) -> int:
        """Count active users."""
        if self._session:
            # Use injected session (testing mode)
            query = select(func.count(User.id)).where(User.is_active.is_(True))
            result = await self._session.execute(query)
            return result.scalar() or 0
        else:
            # Use get_db_session (production mode)
            async with get_db_session() as session:
                query = select(func.count(User.id)).where(User.is_active.is_(True))
                result = await session.execute(query)
                return result.scalar() or 0

    async def update(self, entity: DomainUser) -> DomainUser:
        """Update user entity."""
        async with get_db_session() as session:
            existing = await session.get(User, entity.id)
            if not existing:
                raise ValueError(f"User with id {entity.id} not found")

            # Update the existing entity with new data
            user_model = self._mapper.to_persistence(entity)
            for column in User.__table__.columns:
                if hasattr(user_model, column.name) and column.name != 'id':
                    setattr(existing, column.name, getattr(user_model, column.name))

            await session.flush()
            await session.refresh(existing)
            return self._mapper.to_domain(existing)

    async def find_by_email_for_auth(self, email: str) -> Optional[DomainUser]:
        """Find user by email for authentication purposes."""
        async with get_db_session() as session:
            query = select(User).where(User.email == email)
            result = await session.execute(query)
            user_model = result.scalar_one_or_none()

            if user_model:
                return self._mapper.to_domain(user_model)
            return None

    async def find_by_username_for_auth(self, username: str) -> Optional[DomainUser]:
        """Find user by username for authentication purposes."""
        async with get_db_session() as session:
            query = select(User).where(User.username == username)
            result = await session.execute(query)
            user_model = result.scalar_one_or_none()

            if user_model:
                return self._mapper.to_domain(user_model)
            return None
