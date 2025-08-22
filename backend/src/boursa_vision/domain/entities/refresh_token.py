"""
RefreshToken Entity - Authentication Domain
==========================================

Entity representing a refresh token in the authentication system.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from ..events.auth_events import RefreshTokenCreatedEvent, RefreshTokenRevokedEvent
from .base import AggregateRoot


@dataclass
class RefreshToken(AggregateRoot):
    """
    RefreshToken entity representing a long-lived authentication token.
    
    Manages refresh token lifecycle and validation.
    """
    
    id: UUID = field(default_factory=uuid4)
    token: str = field(default="")
    user_id: UUID = field(default_factory=uuid4)
    expires_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=30))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_used_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_revoked: bool = field(default=False)
    revoke_reason: str = field(default="")
    ip_address: str = field(default="")
    user_agent: str = field(default="")
    
    def __post_init__(self):
        """Initialize aggregate root"""
        super().__init__()
    
    @classmethod
    def create(
        cls,
        token: str,
        user_id: UUID,
        expires_at: datetime,
        ip_address: str = "",
        user_agent: str = "",
    ) -> "RefreshToken":
        """Factory method to create a new refresh token"""
        # Validation
        if not user_id:
            raise ValueError("User ID is required")
        
        if expires_at <= datetime.now(timezone.utc):
            raise ValueError("Expiration date must be in the future")
            
        refresh_token = cls(
            token=token,
            user_id=user_id,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        
        refresh_token._add_domain_event(
            RefreshTokenCreatedEvent(
                user_id=user_id,
                token_id=str(refresh_token.id),
                expires_at=expires_at,
            )
        )
        
        return refresh_token
    
    def is_valid(self) -> bool:
        """Check if the refresh token is still valid"""
        if self.is_revoked:
            return False
        return datetime.now(timezone.utc) < self.expires_at
    
    def is_expired(self) -> bool:
        """Check if the refresh token has expired"""
        return datetime.now(timezone.utc) >= self.expires_at
    
    def revoke(self, reason: str = "manual") -> None:
        """Revoke the refresh token"""
        if self.is_revoked:
            return
            
        self.is_revoked = True
        self.revoke_reason = reason
        self.last_used_at = datetime.now(timezone.utc)  # Update timestamp
        
        self._add_domain_event(
            RefreshTokenRevokedEvent(
                user_id=self.user_id,
                token_id=str(self.id),
                revoke_reason=reason,
            )
        )
    
    def use(self) -> None:
        """Mark the token as used (update last_used_at)"""
        if not self.is_valid():
            raise ValueError("Cannot use invalid or revoked token")
        
        self.last_used_at = datetime.now(timezone.utc)
    
    def __eq__(self, other) -> bool:
        """Equality based on ID"""
        if not isinstance(other, RefreshToken):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID"""
        return hash(self.id)
    
    def __str__(self) -> str:
        return f"RefreshToken(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})"
    
    def __repr__(self) -> str:
        return (
            f"RefreshToken(id={self.id}, user_id={self.user_id}, "
            f"expires_at={self.expires_at}, is_revoked={self.is_revoked})"
        )
