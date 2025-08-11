"""
User Domain Events
==================

Domain events related to user lifecycle and operations.

Classes:
    UserCreatedEvent: Fired when a new user is created.
    UserDeactivatedEvent: Fired when a user is deactivated.
    UserRoleChangedEvent: Fired when a user's role changes.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING
from uuid import UUID

from .portfolio_events import DomainEvent

if TYPE_CHECKING:
    from ..entities.user import UserRole


@dataclass(kw_only=True)
class UserCreatedEvent(DomainEvent):
    """Event fired when a new user is created"""

    user_id: UUID
    email: str
    role: str  # Use string to avoid circular import


@dataclass(kw_only=True)
class UserDeactivatedEvent(DomainEvent):
    """Event fired when a user is deactivated"""

    user_id: UUID
    email: str


@dataclass(kw_only=True)
class UserRoleChangedEvent(DomainEvent):
    """Event fired when a user's role changes"""

    user_id: UUID
    old_role: str  # Use string to avoid circular import
    new_role: str  # Use string to avoid circular import


@dataclass(kw_only=True)
class UserEmailVerifiedEvent(DomainEvent):
    """Event fired when a user's email is verified"""

    user_id: UUID
    email: str


@dataclass(kw_only=True)
class UserTwoFactorEnabledEvent(DomainEvent):
    """Event fired when two-factor authentication is enabled"""

    user_id: UUID
    email: str
