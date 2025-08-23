"""
User Entity - Core Business Domain
==================================

Pure business logic for user management following DDD principles.
No dependencies on external frameworks or infrastructure.

Classes:
    User: Represents a platform user with authentication and profile data.
    UserRole: Enum representing different user roles and permissions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from ..events.user_events import UserCreatedEvent, UserDeactivatedEvent
from ..value_objects.money import Currency
from .base import AggregateRoot


class UserRole(str, Enum):
    """User roles with different permission levels"""

    ADMIN = "admin"
    TRADER = "trader"
    ANALYST = "analyst"
    VIEWER = "viewer"

    @property
    def permissions(self) -> list[str]:
        """Get permissions for this role"""
        permissions_map = {
            self.ADMIN: [
                "create_user",
                "delete_user",
                "manage_system",
                "create_portfolio",
                "delete_portfolio",
                "view_all_portfolios",
                "execute_trades",
                "view_analytics",
                "manage_alerts",
            ],
            self.TRADER: [
                "create_portfolio",
                "manage_own_portfolios",
                "execute_trades",
                "view_analytics",
                "manage_alerts",
            ],
            self.ANALYST: ["view_portfolios", "view_analytics", "create_reports"],
            self.VIEWER: ["view_portfolios", "view_basic_analytics"],
        }
        return permissions_map.get(self, [])


@dataclass(slots=True)
class User(AggregateRoot):
    """
    User aggregate root representing a platform user.

    Manages user authentication, profile, and business rules.
    """

    id: UUID = field(default_factory=uuid4)
    email: str = field(default="")
    username: str = field(default="")
    password_hash: str = field(default="", repr=False)  # Hidden from repr for security
    first_name: str = field(default="")
    last_name: str = field(default="")
    role: UserRole = field(default=UserRole.VIEWER)
    preferred_currency: Currency = field(default=Currency.USD)
    is_active: bool = field(default=True)
    email_verified: bool = field(default=False)
    two_factor_enabled: bool = field(default=False)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    last_login: datetime | None = field(default=None)
    _is_new_user: bool = field(default=False, init=False)  # Internal flag

    def __post_init__(self):
        """Initialize aggregate root and validate user data"""
        AggregateRoot.__init__(self)  # ✅ Appel explicite au lieu de super()
        self._validate()

        # Add domain event if this is a new user
        if hasattr(self, "_is_new_user") and self._is_new_user:
            self._add_domain_event(
                UserCreatedEvent(
                    user_id=self.id, email=self.email, role=self.role.value
                )
            )

    @classmethod
    def create(
        cls,
        email: str,
        username: str,
        password_hash: str,
        first_name: str,
        last_name: str,
        role: UserRole = UserRole.VIEWER,
        preferred_currency: Currency = Currency.USD,
    ) -> User:
        """Factory method to create a new user"""
        user = cls(
            email=email,
            username=username,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            role=role,
            preferred_currency=preferred_currency,
        )
        user._is_new_user = True
        user.__post_init__()
        return user

    def _validate(self) -> None:
        """Validate user business rules"""
        if not self.email or "@" not in self.email:
            raise ValueError("Valid email is required")

        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")

        if not self.first_name:
            raise ValueError("First name is required")

        if not self.last_name:
            raise ValueError("Last name is required")

    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission"""
        if not self.is_active:
            return False
        return permission in self.role.permissions

    def activate(self) -> None:
        """Activate user account"""
        if self.is_active:
            return
        self.is_active = True

    def deactivate(self) -> None:
        """Deactivate user account"""
        if not self.is_active:
            return
        self.is_active = False
        self._add_domain_event(UserDeactivatedEvent(user_id=self.id, email=self.email))

    def verify_email(self) -> None:
        """Mark email as verified"""
        self.email_verified = True

    def enable_two_factor(self) -> None:
        """Enable two-factor authentication"""
        if not self.email_verified:
            raise ValueError("Email must be verified before enabling 2FA")
        self.two_factor_enabled = True

    def disable_two_factor(self) -> None:
        """Disable two-factor authentication"""
        self.two_factor_enabled = False

    def update_last_login(self) -> None:
        """Update last login timestamp"""
        self.last_login = datetime.now(UTC)

    def change_role(self, new_role: UserRole) -> None:
        """Change user role (admin operation)"""
        if self.role == new_role:
            return
        self.role = new_role
        # Could add RoleChangedEvent here if needed

    def update_profile(
        self,
        first_name: str | None = None,
        last_name: str | None = None,
        preferred_currency: Currency | None = None,
    ) -> None:
        """Update user profile information"""
        if first_name is not None:
            if not first_name:
                raise ValueError("First name cannot be empty")
            self.first_name = first_name

        if last_name is not None:
            if not last_name:
                raise ValueError("Last name cannot be empty")
            self.last_name = last_name

        if preferred_currency is not None:
            self.preferred_currency = preferred_currency

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def display_name(self) -> str:
        """Get display name (full name or username)"""
        full_name = self.full_name
        return full_name if full_name else self.username

    def __str__(self) -> str:
        return f"User({self.username}, {self.email})"

    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, username='{self.username}', "
            f"email='{self.email}', role='{self.role.value}')"
        )
