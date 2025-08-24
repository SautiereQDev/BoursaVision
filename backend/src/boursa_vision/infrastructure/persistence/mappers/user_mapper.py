"""
User Mapper - Domain/Persistence Mapping
========================================

Maps between Domain User entities and SQLAlchemy User models.
"""

from boursa_vision.domain.entities.user import User as DomainUser
from boursa_vision.domain.entities.user import UserRole
from boursa_vision.domain.value_objects.money import Currency
from boursa_vision.infrastructure.persistence.models.users import User as UserModel


class SimpleUserMapper:
    """Simple mapper for User entities and models."""

    @staticmethod
    def to_domain(model: UserModel | None) -> DomainUser | None:
        """Convert SQLAlchemy User model to domain User entity."""
        if model is None:
            return None

        return DomainUser(
            id=model.id,
            email=model.email,
            username=model.username,
            password_hash=model.password_hash,
            first_name=model.first_name or "",
            last_name=model.last_name or "",
            role=UserRole(model.role.lower()) if model.role else UserRole.VIEWER,
            preferred_currency=Currency.USD,  # Default for now
            is_active=getattr(model, "is_active", True),
            email_verified=getattr(model, "email_verified", False),  # Use email_verified from actual DB
            two_factor_enabled=False,  # Not in actual DB, default to False
            created_at=model.created_at,
            updated_at=model.updated_at,
            last_login=None,  # Not in actual DB, default to None
        )

    @staticmethod
    def to_persistence(domain_user: DomainUser | None) -> UserModel | None:
        """Convert domain User entity to SQLAlchemy User model."""
        if domain_user is None:
            return None

        # Create model with only the basic fields that exist in both DB and model
        model = UserModel(
            id=domain_user.id,
            email=domain_user.email,
            username=domain_user.username,
            password_hash=domain_user.password_hash,
            role=domain_user.role.value.upper(),
            is_active=domain_user.is_active,
        )
        
        # Set optional fields that might exist
        if hasattr(model, 'first_name'):
            model.first_name = domain_user.first_name
        if hasattr(model, 'last_name'):
            model.last_name = domain_user.last_name
        if hasattr(model, 'email_verified'):
            model.email_verified = domain_user.email_verified
        elif hasattr(model, 'is_verified'):
            model.is_verified = domain_user.email_verified
        if hasattr(model, 'created_at'):
            model.created_at = domain_user.created_at
        if hasattr(model, 'updated_at'):
            model.updated_at = domain_user.updated_at
            
        return model

    @staticmethod
    def update_model(model: UserModel, domain_user: DomainUser) -> None:
        """Update existing SQLAlchemy model with domain entity data."""
        model.email = domain_user.email
        model.username = domain_user.username
        model.password_hash = domain_user.password_hash
        model.first_name = domain_user.first_name
        model.last_name = domain_user.last_name
        model.role = domain_user.role.value.upper()
        model.is_active = domain_user.is_active
        model.email_verified = domain_user.email_verified  # Use actual DB field name
        # Note: Don't update created_at, but updated_at will be updated automatically

    @classmethod
    def to_model(cls, domain_user: DomainUser | None) -> UserModel | None:
        """Alias for to_persistence for test compatibility."""
        return cls.to_persistence(domain_user)
