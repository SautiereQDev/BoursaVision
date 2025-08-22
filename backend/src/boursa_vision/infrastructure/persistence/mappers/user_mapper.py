"""
User Mapper - Domain/Persistence Mapping
========================================

Maps between Domain User entities and SQLAlchemy User models.
"""

from typing import Optional

from boursa_vision.domain.entities.user import User as DomainUser, UserRole
from boursa_vision.domain.value_objects.money import Currency
from boursa_vision.infrastructure.persistence.models.users import User as UserModel


class SimpleUserMapper:
    """Simple mapper for User entities and models."""

    @staticmethod
    def to_domain(model: Optional[UserModel]) -> Optional[DomainUser]:
        """Convert SQLAlchemy User model to domain User entity."""
        if model is None:
            return None

        return DomainUser(
            id=model.id,
            email=model.email,
            username=model.username,
            password_hash=model.password_hash,  # Model uses password_hash
            first_name=model.first_name or "",
            last_name=model.last_name or "",
            role=UserRole(model.role.lower()) if model.role else UserRole.BASIC,
            preferred_currency=Currency(model.preferred_currency) if hasattr(model, 'preferred_currency') and model.preferred_currency else Currency.USD,
            is_active=getattr(model, 'is_active', True),
            email_verified=getattr(model, 'email_verified', False),
            two_factor_enabled=getattr(model, 'two_factor_enabled', False),
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login=getattr(model, 'last_login', None),
        )

    @staticmethod
    def to_persistence(domain_user: Optional[DomainUser]) -> Optional[UserModel]:
        """Convert domain User entity to SQLAlchemy User model."""
        if domain_user is None:
            return None

        return UserModel(
            id=domain_user.id,
            email=domain_user.email,
            username=domain_user.username,
            password_hash=domain_user.password_hash,  # Domain uses password_hash too
            first_name=domain_user.first_name,
            last_name=domain_user.last_name,
            role=domain_user.role.value.upper(),
            is_active=domain_user.is_active,
            email_verified=domain_user.email_verified,
            two_factor_enabled=domain_user.two_factor_enabled,
            created_at=domain_user.created_at,
            updated_at=domain_user.updated_at,
            last_login=domain_user.last_login,
        )

    @classmethod
    def to_model(cls, domain_user: Optional[DomainUser]) -> Optional[UserModel]:
        """Alias for to_persistence for test compatibility."""
        return cls.to_persistence(domain_user)
