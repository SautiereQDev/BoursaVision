"""
SQLAlchemy RefreshToken Repository Implementation
===============================================

Repository implementation for RefreshToken entity using SQLAlchemy.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from boursa_vision.domain.entities.refresh_token import (
    RefreshToken as DomainRefreshToken,
)
from boursa_vision.domain.repositories.refresh_token_repository import (
    IRefreshTokenRepository,
)
from boursa_vision.infrastructure.persistence.models.refresh_tokens import RefreshToken


class SQLAlchemyRefreshTokenRepository(IRefreshTokenRepository):
    """SQLAlchemy implementation of refresh token repository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session

    async def find_by_id(self, entity_id: UUID) -> DomainRefreshToken | None:
        """Find refresh token by ID"""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def save(self, entity: DomainRefreshToken) -> DomainRefreshToken:
        """Save refresh token (create or update)"""
        existing = await self.find_by_id(entity.id)

        if existing:
            return await self.update(entity)

        # Create new
        model = self._to_persistence(entity)
        self.session.add(model)
        await self.session.flush()  # Get ID without committing

        return self._to_domain(model)

    async def update(self, entity: DomainRefreshToken) -> DomainRefreshToken:
        """Update existing refresh token"""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.id == entity.id)
        )
        model = result.scalar_one_or_none()

        if not model:
            raise ValueError(f"RefreshToken with ID {entity.id} not found")

        self._update_model(model, entity)
        await self.session.flush()

        return self._to_domain(model)

    async def delete(self, entity_id: UUID) -> bool:
        """Delete refresh token by ID"""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.id == entity_id)
        )
        model = result.scalar_one_or_none()

        if model:
            await self.session.delete(model)
            return True

        return False

    async def find_by_token(self, token: str) -> DomainRefreshToken | None:
        """Find refresh token by token string"""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def find_by_user_id(self, user_id: UUID) -> list[DomainRefreshToken]:
        """Find all refresh tokens for a user"""
        result = await self.session.execute(
            select(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .order_by(RefreshToken.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def find_active_by_user_id(self, user_id: UUID) -> list[DomainRefreshToken]:
        """Find all active (non-revoked, non-expired) refresh tokens for a user"""
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(RefreshToken)
            .where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked is False,
                    RefreshToken.expires_at > now,
                )
            )
            .order_by(RefreshToken.created_at.desc())
        )
        models = result.scalars().all()
        return [self._to_domain(model) for model in models]

    async def revoke_all_for_user(
        self, user_id: UUID, reason: str = "logout_all"
    ) -> int:
        """Revoke all refresh tokens for a user, returns count of revoked tokens"""
        result = await self.session.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked is False,
                )
            )
        )
        models = result.scalars().all()

        count = 0
        for model in models:
            model.is_revoked = True
            model.revoke_reason = reason
            count += 1

        await self.session.flush()
        return count

    async def cleanup_expired_tokens(self, before_date: datetime) -> int:
        """Clean up expired tokens before given date, returns count of deleted tokens"""
        result = await self.session.execute(
            select(RefreshToken).where(RefreshToken.expires_at < before_date)
        )
        models = result.scalars().all()

        count = len(models)
        for model in models:
            await self.session.delete(model)

        await self.session.flush()
        return count

    async def count_active_sessions(self, user_id: UUID) -> int:
        """Count active sessions (valid refresh tokens) for a user"""
        now = datetime.now(UTC)
        result = await self.session.execute(
            select(RefreshToken).where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked is False,
                    RefreshToken.expires_at > now,
                )
            )
        )
        models = result.scalars().all()
        return len(models)

    def _to_domain(self, model: RefreshToken) -> DomainRefreshToken:
        """Convert SQLAlchemy model to domain entity"""
        return DomainRefreshToken(
            id=model.id,
            token=model.token,
            user_id=model.user_id,
            expires_at=model.expires_at,
            created_at=model.created_at,
            last_used_at=model.last_used_at,
            is_revoked=model.is_revoked,
            revoke_reason=model.revoke_reason or "",
            ip_address=model.ip_address or "",
            user_agent=model.user_agent or "",
        )

    def _to_persistence(self, entity: DomainRefreshToken) -> RefreshToken:
        """Convert domain entity to SQLAlchemy model"""
        return RefreshToken(
            id=entity.id,
            token=entity.token,
            user_id=entity.user_id,
            expires_at=entity.expires_at,
            created_at=entity.created_at,
            last_used_at=entity.last_used_at,
            is_revoked=entity.is_revoked,
            revoke_reason=entity.revoke_reason if entity.revoke_reason else None,
            ip_address=entity.ip_address if entity.ip_address else None,
            user_agent=entity.user_agent if entity.user_agent else None,
        )

    def _update_model(self, model: RefreshToken, entity: DomainRefreshToken) -> None:
        """Update SQLAlchemy model from domain entity"""
        model.token = entity.token
        model.user_id = entity.user_id
        model.expires_at = entity.expires_at
        model.last_used_at = entity.last_used_at
        model.is_revoked = entity.is_revoked
        model.revoke_reason = entity.revoke_reason if entity.revoke_reason else None
        model.ip_address = entity.ip_address if entity.ip_address else None
        model.user_agent = entity.user_agent if entity.user_agent else None
