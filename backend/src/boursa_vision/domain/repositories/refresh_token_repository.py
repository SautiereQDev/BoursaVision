"""
RefreshToken Repository Interface
=================================

Repository interface for refresh token aggregate following DDD patterns.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from ..entities.refresh_token import RefreshToken
from .base_repository import IBaseRepository


class IRefreshTokenRepository(IBaseRepository[RefreshToken], ABC):
    """Interface for refresh token repository operations"""

    @abstractmethod
    async def find_by_token(self, token: str) -> RefreshToken | None:
        """Find refresh token by token string"""
        raise NotImplementedError

    @abstractmethod
    async def find_by_user_id(self, user_id: UUID) -> list[RefreshToken]:
        """Find all refresh tokens for a user"""
        raise NotImplementedError

    @abstractmethod
    async def find_active_by_user_id(self, user_id: UUID) -> list[RefreshToken]:
        """Find all active (non-revoked, non-expired) refresh tokens for a user"""
        raise NotImplementedError

    @abstractmethod
    async def revoke_all_for_user(
        self, user_id: UUID, reason: str = "logout_all"
    ) -> int:
        """Revoke all refresh tokens for a user, returns count of revoked tokens"""
        raise NotImplementedError

    @abstractmethod
    async def cleanup_expired_tokens(self, before_date: datetime) -> int:
        """Clean up expired tokens before given date, returns count of deleted tokens"""
        raise NotImplementedError

    @abstractmethod
    async def count_active_sessions(self, user_id: UUID) -> int:
        """Count active sessions (valid refresh tokens) for a user"""
        raise NotImplementedError
