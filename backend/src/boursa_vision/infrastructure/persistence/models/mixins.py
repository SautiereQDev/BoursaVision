"""
Mixins for SQLAlchemy models.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID


class PortfolioInstrumentMixin:
    """
    Mixin providing common foreign key columns for portfolio and instrument
    relationships.

    This mixin provides standard columns that appear frequently across models
    that reference portfolios and instruments.
    """

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    portfolio_id = Column(
        UUID(as_uuid=True),
        ForeignKey("portfolios.id", ondelete="CASCADE"),
        nullable=False,
    )
    instrument_id = Column(
        UUID(as_uuid=True), ForeignKey("instruments.id"), nullable=False
    )
    symbol = Column(String(20), nullable=False)


class TimestampMixin:
    """
    Mixin class to add timestamp fields to a database model.

    Attributes:
        created_at (Column): A timestamp column that stores the creation time
        of the record.
                             Defaults to the current UTC time.
        updated_at (Column): A timestamp column that stores the last update
        time of the record.
                             Defaults to the current UTC time and updates
                             automatically on record modification.
    """

    created_at = Column(TIMESTAMP, default=lambda: datetime.now(UTC))
    updated_at = Column(
        TIMESTAMP,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def touch(self):
        """
        Updates the `updated_at` timestamp to the current UTC time.
        """
        self.updated_at = datetime.now(UTC)
