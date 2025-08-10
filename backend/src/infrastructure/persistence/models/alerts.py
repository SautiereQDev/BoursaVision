
"""
SQLAlchemy models for alerts and notifications.
"""
# ================================================================
# TRADING PLATFORM - ALERTS AND NOTIFICATIONS MODELS
# SQLAlchemy models for the alerts system
# ================================================================

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import relationship

from .base import Base, DatabaseMixin
from .mixins import TimestampMixin

# Constants
ON_DELETE_SET_NULL = "SET NULL"
USERS_ID = "users.id"
PORTFOLIOS_ID = "portfolios.id"
ALERT_ID = "alerts.id"


class Alert(Base, DatabaseMixin, TimestampMixin):
    """
    Alerts configured by users.

    This model represents alerts that users can configure to monitor specific
    conditions in their portfolios or the market. Alerts can be based on price,
    volume, signals, or portfolio-level metrics. Each alert is associated with
    a user and optionally a portfolio.

    Attributes:
        id (UUID): Unique identifier for the alert.
        user_id (UUID): Identifier of the user who created the alert.
        portfolio_id (UUID): Identifier of the associated portfolio (if any).
        symbol (str): The financial instrument symbol the alert is monitoring.
        alert_type (str): The type of alert (e.g., PRICE, VOLUME, SIGNAL,
            PORTFOLIO).
        condition_type (str): The condition type (e.g., ABOVE, BELOW, EQUALS,
            CHANGE_PCT).
        threshold_value (Decimal): The threshold value for the alert condition.
        threshold_percentage (Decimal): The threshold percentage for the alert
            condition.
        current_value (Decimal): The current value of the monitored metric.
        message_template (str): Template for the alert message.
        notification_methods (JSONB): Methods to notify the user (e.g., email,
            SMS).
        is_active (bool): Whether the alert is currently active.
        is_triggered (bool): Whether the alert has been triggered.
        trigger_count (int): Number of times the alert has been triggered.
        last_triggered_at (datetime): Timestamp of the last trigger.
        created_at (datetime): Timestamp when the alert was created.
        updated_at (datetime): Timestamp when the alert was last updated.

    Relationships:
        user: The user who created the alert.
        portfolio: The portfolio associated with the alert.
        notifications: Notifications generated for this alert.
    """

    __tablename__ = "alerts"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID,
        ForeignKey(USERS_ID, ondelete=ON_DELETE_SET_NULL),
    )
    portfolio_id = Column(UUID, ForeignKey(PORTFOLIOS_ID, ondelete=ON_DELETE_SET_NULL))
    symbol = Column(String(20))
    alert_type = Column(String(20), nullable=False)
    condition_type = Column(String(10), nullable=False)
    threshold_value = Column(Numeric(15, 4))
    threshold_percentage = Column(Numeric(5, 2))
    current_value = Column(Numeric(15, 4))
    message_template = Column(Text)
    notification_methods = Column(JSONB)
    is_active = Column(Boolean, default=True)
    is_triggered = Column(Boolean, default=False)
    trigger_count = Column(Integer, default=0)
    last_triggered_at = Column(TIMESTAMP)
    # created_at, updated_at fournis par TimestampMixin
    title = Column(String(255))  # New field for title
    description = Column(Text)  # New field for description

    # Relations
    user = relationship("User", back_populates="alerts")
    portfolio = relationship("Portfolio", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert")

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ('PRICE', 'VOLUME', 'SIGNAL', 'PORTFOLIO')",
            name="check_alert_type",
        ),
        CheckConstraint(
            "condition_type IN ('ABOVE', 'BELOW', 'EQUALS', 'CHANGE_PCT')",
            name="check_condition_type",
        ),
        Index("idx_alerts_user", "user_id"),
        Index("idx_alerts_active", "is_active"),
        Index("idx_alerts_symbol", "symbol"),
    )


class Notification(Base, DatabaseMixin):
    """
    Notifications sent to users.

    This model represents notifications that are sent to users based on alerts
    or other system events. Notifications can be of various types, such as
    alerts, signals, system messages, or marketing messages.

    Attributes:
        id (UUID): Unique identifier for the notification.
        user_id (UUID): Identifier of the user receiving the notification.
        alert_id (UUID): Identifier of the associated alert (if any).
        type (str): The type of notification (e.g., ALERT, SIGNAL, SYSTEM,
            MARKETING).
        title (str): The title of the notification.
        message (str): The content of the notification message.
        data (JSONB): Additional data related to the notification.
        channels (JSONB): Channels through which the notification was sent
            (e.g., email, SMS).
        is_read (bool): Whether the notification has been read by the user.
        read_at (datetime): Timestamp when the notification was read.
        sent_at (datetime): Timestamp when the notification was sent.
        created_at (datetime): Timestamp when the notification was created.

    Relationships:
        user: The user receiving the notification.
        alert: The alert associated with the notification.
    """

    __tablename__ = "notifications"

    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID,
        ForeignKey(USERS_ID, ondelete=ON_DELETE_SET_NULL),
    )
    alert_id = Column(UUID, ForeignKey(ALERT_ID, ondelete=ON_DELETE_SET_NULL))
    type = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    data = Column(JSONB)
    channels = Column(JSONB)
    is_read = Column(Boolean, default=False)
    read_at = Column(TIMESTAMP)
    sent_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))
    created_at = Column(TIMESTAMP, default=lambda: datetime.now(timezone.utc))

    # Relations
    user = relationship("User", back_populates="notifications")
    alert = relationship("Alert", back_populates="notifications")

    __table_args__ = (
        CheckConstraint(
            "type IN ('ALERT', 'SIGNAL', 'SYSTEM', 'MARKETING')",
            name="check_notification_type",
        ),
        Index("idx_notifications_user", "user_id"),
        Index("idx_notifications_unread", "user_id", "is_read"),
    )
