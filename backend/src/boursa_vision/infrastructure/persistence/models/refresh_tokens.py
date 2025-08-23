"""
Refresh Token Models
===================

SQLAlchemy models for refresh token management.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import TIMESTAMP, Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, DatabaseMixin


class RefreshToken(Base, DatabaseMixin):
    """Refresh token model for JWT authentication"""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = Column(Text, unique=True, nullable=False, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False, index=True)
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    last_used_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    is_revoked = Column(Boolean, default=False, nullable=False, index=True)
    revoke_reason = Column(String(100))
    ip_address = Column(String(45))  # Support both IPv4 and IPv6
    user_agent = Column(Text)

    # Relationship to User
    user = relationship("User", back_populates="refresh_tokens")

    __table_args__ = (
        Index("idx_refresh_tokens_user_active", "user_id", "is_revoked"),
        Index("idx_refresh_tokens_expires", "expires_at"),
        Index("idx_refresh_tokens_token_active", "token", "is_revoked"),
    )

    def __repr__(self) -> str:
        return (
            f"RefreshToken(id={self.id}, user_id={self.user_id}, "
            f"expires_at={self.expires_at}, is_revoked={self.is_revoked})"
        )
