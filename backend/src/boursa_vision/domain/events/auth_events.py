"""
Authentication Domain Events
============================

Domain events related to authentication and authorization operations.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .portfolio_events import DomainEvent


@dataclass(kw_only=True)
class UserLoggedInEvent(DomainEvent):
    """Event fired when a user successfully logs in"""

    user_id: UUID
    email: str
    login_method: str  # "password", "2fa", "refresh_token"
    ip_address: str
    user_agent: str


@dataclass(kw_only=True)
class UserLoggedOutEvent(DomainEvent):
    """Event fired when a user logs out"""

    user_id: UUID
    email: str
    logout_method: str  # "manual", "token_expired", "admin_force"


@dataclass(kw_only=True)
class UserLoginFailedEvent(DomainEvent):
    """Event fired when a user login attempt fails"""

    email: str
    failure_reason: str  # "invalid_credentials", "account_locked", "account_disabled"
    ip_address: str
    user_agent: str


@dataclass(kw_only=True)
class RefreshTokenCreatedEvent(DomainEvent):
    """Event fired when a refresh token is created"""

    user_id: UUID
    token_id: str
    expires_at: datetime


@dataclass(kw_only=True)
class RefreshTokenRevokedEvent(DomainEvent):
    """Event fired when a refresh token is revoked"""

    user_id: UUID
    token_id: str
    revoke_reason: str  # "logout", "token_rotation", "security_breach"


@dataclass(kw_only=True)
class AccessTokenCreatedEvent(DomainEvent):
    """Event fired when an access token is created"""

    user_id: UUID
    token_id: str
    expires_at: datetime
    scopes: list[str]


@dataclass(kw_only=True)
class PasswordChangedEvent(DomainEvent):
    """Event fired when a user's password is changed"""

    user_id: UUID
    email: str
    changed_by: str  # "user", "admin", "password_reset"


@dataclass(kw_only=True)
class TwoFactorEnabledEvent(DomainEvent):
    """Event fired when two-factor authentication is enabled"""

    user_id: UUID
    email: str
    method: str  # "totp", "sms", "email"


@dataclass(kw_only=True)
class TwoFactorDisabledEvent(DomainEvent):
    """Event fired when two-factor authentication is disabled"""

    user_id: UUID
    email: str
    disabled_by: str  # "user", "admin"
