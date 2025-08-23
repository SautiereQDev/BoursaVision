"""Create market_data_archive table

Revision ID: 001_market_data_archive
Revises: 
Create Date: 2025-08-14 22:45:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001_market_data_archive"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create market_data_archive table and hypertable."""

    # Enable TimescaleDB extension
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")

    # Create market_data_archive table
    op.create_table(
        "market_data_archive",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("symbol", sa.String(20), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("high_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("low_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("close_price", sa.Numeric(20, 8), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True),
        sa.Column("interval_type", sa.String(10), nullable=False, server_default="1d"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "symbol", "timestamp", "interval_type", name="uix_symbol_timestamp_interval"
        ),
    )

    # Create indexes
    op.create_index("idx_market_data_archive_symbol", "market_data_archive", ["symbol"])
    op.create_index(
        "idx_market_data_archive_timestamp", "market_data_archive", ["timestamp"]
    )
    op.create_index(
        "idx_market_data_archive_symbol_timestamp",
        "market_data_archive",
        ["symbol", "timestamp"],
    )

    # Convert to TimescaleDB hypertable
    op.execute(
        """
        SELECT create_hypertable(
            'market_data_archive', 
            'timestamp',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
    """
    )

    # Create compression policy (compress data older than 7 days)
    op.execute(
        """
        ALTER TABLE market_data_archive SET (
            timescaledb.compress,
            timescaledb.compress_segmentby = 'symbol',
            timescaledb.compress_orderby = 'timestamp DESC'
        );
    """
    )

    op.execute(
        """
        SELECT add_compression_policy('market_data_archive', INTERVAL '7 days');
    """
    )


def downgrade() -> None:
    """Drop market_data_archive table."""
    op.drop_table("market_data_archive")
