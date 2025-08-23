"""
SQLAlchemy models for system audit and configuration.
"""
# ================================================================
# PLATEFORME TRADING - MODELES SYSTEME
# Modèles SQLAlchemy pour l'audit et la configuration système
# ================================================================

import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID

from .base import Base, DatabaseMixin


class AuditLog(Base, DatabaseMixin):
    """Logs d'audit des actions utilisateur"""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    action = Column(String(50), nullable=False)
    resource_type = Column(String(30))
    resource_id = Column(UUID(as_uuid=True))
    old_values = Column(JSONB)
    new_values = Column(JSONB)
    # Changed from INET to String for SQLite compatibility
    ip_address = Column(String(45))
    user_agent = Column(Text)
    success = Column(Boolean, default=True)
    error_message = Column(Text)
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(UTC))

    __table_args__ = (
        Index("idx_audit_logs_user", "user_id", "created_at"),
        Index("idx_audit_logs_action", "action", "created_at"),
    )


class SystemConfig(Base, DatabaseMixin):
    """Configuration système"""

    __tablename__ = "system_config"

    key = Column(String(100), primary_key=True)
    value = Column(JSONB, nullable=False)
    description = Column(Text)
    is_encrypted = Column(Boolean, default=False)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    updated_at = Column(
        TIMESTAMP,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    __table_args__ = (Index("idx_system_config_key", "key"),)
