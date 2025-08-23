"""
Authentication Value Objects
===========================

Value objects for authentication-related concepts in the domain layer.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID


@dataclass(frozen=True)
class RefreshToken:
    """Value object representing a refresh token"""

    token: str
    user_id: UUID
    expires_at: datetime
    created_at: datetime
    is_revoked: bool = False

    def __post_init__(self):
        """Validate refresh token data after initialization"""
        if not self.token or not self.token.strip():
            raise ValueError("Token cannot be empty")
        if self.expires_at <= datetime.now(UTC):
            raise ValueError("Token cannot be expired")

    def is_valid(self) -> bool:
        """Check if the refresh token is still valid"""
        if self.is_revoked:
            return False
        return datetime.now(UTC) < self.expires_at

    def is_expired(self) -> bool:
        """Check if the refresh token has expired"""
        return datetime.now(UTC) >= self.expires_at


@dataclass(frozen=True)
class AccessToken:
    """Value object representing an access token"""

    token: str
    user_id: UUID
    expires_at: datetime
    issued_at: datetime
    token_type: str = "Bearer"

    def __post_init__(self):
        """Validate access token data after initialization"""
        if not self.token or not self.token.strip():
            raise ValueError("Token cannot be empty")
        if self.expires_at <= datetime.now(UTC):
            raise ValueError("Token cannot be expired")

    def is_valid(self) -> bool:
        """Check if the access token is still valid"""
        return datetime.now(UTC) < self.expires_at

    def is_expired(self) -> bool:
        """Check if the access token has expired"""
        return datetime.now(UTC) >= self.expires_at

    def expires_in_seconds(self) -> int:
        """Get seconds until expiration"""
        now = datetime.now(UTC)
        if self.expires_at <= now:
            return 0
        return int((self.expires_at - now).total_seconds())

    @property
    def expires_in(self) -> int:
        """Get seconds until expiration (property version)"""
        return self.expires_in_seconds()


@dataclass(frozen=True)
class TokenPair:
    """Value object representing an access and refresh token pair"""

    access_token: AccessToken
    refresh_token: RefreshToken

    def __post_init__(self):
        """Validate token pair data after initialization"""
        if self.access_token is None:
            raise ValueError("Access token is required")
        if self.refresh_token is None:
            raise ValueError("Refresh token is required")

    def is_valid(self) -> bool:
        """Check if both tokens are valid"""
        return self.access_token.is_valid() and self.refresh_token.is_valid()
