"""
User Entity - Core Business Domain
==================================

Pure business logic for user management following DDD principles.
No dependencies on external frameworks or infrastructure.

Classes:
    User: Represents a platform user with authentication and profile data.
    UserRole: Enum representing different user roles and permissions.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from ..events.user_events import UserCreatedEvent, UserDeactivatedEvent
from ..value_objects.money import Currency
from .base import AggregateRoot


class UserRole(str, Enum):
    """User roles with different permission levels"""

    ADMIN = "admin"
    PREMIUM = "premium" 
    BASIC = "basic"

    @property
    def permissions(self) -> List[str]:
        """Get permissions for this role with hierarchical inheritance"""
        # Base permissions for each role
        role_permissions = {
            UserRole.BASIC: [
                "view_analytics",
                "view_basic_analytics",
                "view_portfolios", 
                "create_basic_portfolio",
                "view_public_data",
            ],
            UserRole.PREMIUM: [
                "create_portfolio",
                "manage_own_portfolios", 
                "execute_trades",
                "view_analytics",
                "view_advanced_analytics",
                "manage_alerts",
                "access_premium_features",
                "export_data",
                "real_time_data",
            ],
            UserRole.ADMIN: [
                "create_user",
                "delete_user", 
                "manage_system",
                "delete_portfolio",
                "view_all_portfolios",
                "access_admin_panel",
                "manage_user_roles",
                "view_system_metrics",
            ],
        }
        
        # Get permissions with hierarchy
        permissions = []
        
        if self == UserRole.ADMIN:
            # Admin gets all permissions
            permissions.extend(role_permissions[UserRole.BASIC])
            permissions.extend(role_permissions[UserRole.PREMIUM])
            permissions.extend(role_permissions[UserRole.ADMIN])
        elif self == UserRole.PREMIUM:
            # Premium gets basic + premium permissions
            permissions.extend(role_permissions[UserRole.BASIC])
            permissions.extend(role_permissions[UserRole.PREMIUM])
        else:  # BASIC
            permissions.extend(role_permissions[UserRole.BASIC])
        
        return permissions


@dataclass
class User(AggregateRoot):
    """
    User aggregate root representing a platform user.

    Manages user authentication, profile, and business rules.
    """

    id: UUID = field(default_factory=uuid4)
    email: str = field(default="")
    username: str = field(default="")
    password_hash: str = field(default="", repr=False)  # Hide from repr for security
    first_name: str = field(default="")
    last_name: str = field(default="")
    role: UserRole = field(default=UserRole.BASIC)
    preferred_currency: Currency = field(default=Currency.USD)
    is_active: bool = field(default=True)
    email_verified: bool = field(default=False)
    two_factor_enabled: bool = field(default=False)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = field(default=None)

    def __post_init__(self):
        """Initialize aggregate root and validate user data"""
        super().__init__()
        self._validate()

        # Add domain event if this is a new user
        if hasattr(self, "_is_new_user") and getattr(self, "_is_new_user", False):
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
        role: UserRole = UserRole.BASIC,
        preferred_currency: Currency = Currency.USD,
    ) -> "User":
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
        # Mark as new user for event handling
        setattr(user, "_is_new_user", True)
        user.__post_init__()
        return user

    def _validate(self) -> None:
        """Validate user business rules"""
        if not self.email:
            raise ValueError("Email is required")
        elif "@" not in self.email:
            raise ValueError("Invalid email format")

        if not self.username or len(self.username) < 3:
            raise ValueError("Username must be at least 3 characters")

        if not self.first_name:
            raise ValueError("First name is required")

        if not self.last_name:
            raise ValueError("Last name is required")
        
        # Only validate password_hash if user has one (for new users)
        if hasattr(self, "_is_new_user") and getattr(self, "_is_new_user", False):
            if not self.password_hash:
                raise ValueError("Password hash is required for new users")

    def __eq__(self, other) -> bool:
        """Two users are equal if they have the same ID"""
        if not isinstance(other, User):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID for proper set/dict behavior"""
        return hash(self.id)

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
        self.last_login = datetime.now(timezone.utc)

    def change_password(self, new_password_hash: str) -> None:
        """Change user password hash"""
        if not new_password_hash:
            raise ValueError("Password hash cannot be empty")
        self.password_hash = new_password_hash
        self.updated_at = datetime.now(timezone.utc)

    def change_role(self, new_role: UserRole) -> None:
        """Change user role (admin operation)"""
        if self.role == new_role:
            return
        self.role = new_role
        # Could add RoleChangedEvent here if needed

    def update_profile(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        preferred_currency: Optional[Currency] = None,
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
        return f"User({self.username}, {self.email}, {self.first_name} {self.last_name})"

    def __repr__(self) -> str:
        return (
            f"User(id={self.id}, username='{self.username}', "
            f"email='{self.email}', role='{self.role.value}')"
        )
