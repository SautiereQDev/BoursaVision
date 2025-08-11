"""
User Models
===========

This module contains SQLAlchemy models for managing user-related data in the trading platform.
"""

# ================================================================
# TRADING PLATFORM - USER MODELS
# SQLAlchemy models for user management
# ================================================================

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import Base, DatabaseMixin
from .enums import RiskTolerance

CASCADE_ALL_DELETE_ORPHAN = "all, delete-orphan"


class User(Base, DatabaseMixin):
    """User model with investor profile"""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), default="VIEWER", nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone = Column(String(20))
    date_of_birth = Column(Date)
    country = Column(String(2))  # Code ISO pays
    timezone = Column(String(50), default="UTC")
    language = Column(String(5), default="en")
    is_active = Column(Boolean, default=True, index=True)
    is_verified = Column(Boolean, default=False)
    risk_tolerance = Column(
        String(20),
        default=RiskTolerance.MODERATE,
    )
    # Investor experience level: beginner, intermediate, advanced
    investment_experience = Column(
        String(20),
        nullable=False,
        default="beginner",
    )
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    last_login_at = Column(
        TIMESTAMP(timezone=True),
    )
    portfolios = relationship(
        "Portfolio", back_populates="user", cascade=CASCADE_ALL_DELETE_ORPHAN
    )
    alerts = relationship(
        "Alert", back_populates="user", cascade=CASCADE_ALL_DELETE_ORPHAN
    )
    notifications = relationship(
        "Notification",
        back_populates="user",
        cascade=CASCADE_ALL_DELETE_ORPHAN,
    )
    sessions = relationship(
        "UserSession", back_populates="user", cascade=CASCADE_ALL_DELETE_ORPHAN
    )

    __table_args__ = (
        CheckConstraint(
            "risk_tolerance IN ('conservative', 'moderate', 'aggressive')",
            name="check_risk_tolerance",
        ),
        CheckConstraint(
            "investment_experience IN ('beginner', 'intermediate', 'advanced')",
            name="check_investment_experience",
        ),
        CheckConstraint(
            "role IN ('ADMIN', 'TRADER', 'ANALYST', 'VIEWER')",
            name="check_user_role",
        ),
    )

    def get_default_portfolio(self):
        """Retourne le portfolio par défaut de l'utilisateur"""
        return next((p for p in self.portfolios if p.is_default), None)

    def get_active_portfolios(self):
        """Retourne les portfolios actifs"""
        return [p for p in self.portfolios if p.is_active]


class UserSession(Base, DatabaseMixin):
    """User sessions for authentication"""

    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_token = Column(String(255), unique=True, nullable=False)
    refresh_token = Column(String(255), unique=True)
    # Changed from INET to String for SQLite compatibility
    ip_address = Column(String(45))
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    created_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    last_activity_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="sessions")
    __table_args__ = (
        Index("idx_user_sessions_user", "user_id"),
        Index("idx_user_sessions_token", "session_token"),
        Index("idx_user_sessions_expires", "expires_at"),
    )
