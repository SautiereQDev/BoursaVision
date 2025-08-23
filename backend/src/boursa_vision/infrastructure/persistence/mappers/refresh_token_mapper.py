"""
RefreshToken Mapper - Domain to Persistence
==========================================

Mapper for RefreshToken domain entity ↔ SQLAlchemy model.
"""

from boursa_vision.domain.entities.refresh_token import (
    RefreshToken as DomainRefreshToken,
)
from boursa_vision.infrastructure.persistence.models.refresh_tokens import RefreshToken


class RefreshTokenMapper:
    """Mapper for RefreshToken domain entity ↔ SQLAlchemy model."""

    @staticmethod
    def to_domain(model: RefreshToken) -> DomainRefreshToken:
        """Convert SQLAlchemy RefreshToken model to domain RefreshToken entity."""
        domain_entity = DomainRefreshToken(
            id=model.id,
            token=model.token,
            user_id=model.user_id,
            expires_at=model.expires_at,
            created_at=model.created_at,
            last_used_at=model.last_used_at,
            is_revoked=model.is_revoked,
            revoke_reason=model.revoke_reason or "",
            ip_address=model.ip_address or "",
            user_agent=model.user_agent or "",
        )
        return domain_entity

    @staticmethod
    def to_persistence(entity: DomainRefreshToken) -> RefreshToken:
        """Convert domain RefreshToken entity to SQLAlchemy RefreshToken model."""
        return RefreshToken(
            id=entity.id,
            token=entity.token,
            user_id=entity.user_id,
            expires_at=entity.expires_at,
            created_at=entity.created_at,
            last_used_at=entity.last_used_at,
            is_revoked=entity.is_revoked,
            revoke_reason=entity.revoke_reason if entity.revoke_reason else None,
            ip_address=entity.ip_address if entity.ip_address else None,
            user_agent=entity.user_agent if entity.user_agent else None,
        )

    @staticmethod
    def update_model(model: RefreshToken, entity: DomainRefreshToken) -> None:
        """Update SQLAlchemy model from domain entity."""
        model.token = entity.token
        model.user_id = entity.user_id
        model.expires_at = entity.expires_at
        model.last_used_at = entity.last_used_at
        model.is_revoked = entity.is_revoked
        model.revoke_reason = entity.revoke_reason if entity.revoke_reason else None
        model.ip_address = entity.ip_address if entity.ip_address else None
        model.user_agent = entity.user_agent if entity.user_agent else None
