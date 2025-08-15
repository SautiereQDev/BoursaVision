"""Create TimescaleDB hypertables and performance optimizations

Revision ID: 001_timescaledb_setup
Revises: 
Create Date: 2025-08-11 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op
from boursa_vision.infrastructure.persistence.alembic.timescaledb_utils import (
    add_compression_policy,
    add_retention_policy,
    create_hypertable,
    create_performance_indexes,
)

# revision identifiers, used by Alembic.
revision: str = "001_timescaledb_setup"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade: Create hypertables and performance optimizations."""

    # Enable TimescaleDB extension
    op.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))

    # Create hypertables for time-series data

    # 1. Market Data Hypertable
    create_hypertable(
        table_name="market_data",
        time_column="time",
        partitioning_column="symbol",
        chunk_time_interval="1 day",
        number_partitions=4,
    )

    # 2. Technical Indicators Hypertable
    create_hypertable(
        table_name="technical_indicators",
        time_column="time",
        partitioning_column="symbol",
        chunk_time_interval="1 day",
        number_partitions=4,
    )

    # 3. Signals Hypertable
    create_hypertable(
        table_name="signals",
        time_column="time",
        partitioning_column="symbol",
        chunk_time_interval="1 day",
        number_partitions=4,
    )

    # 4. Portfolio Performance Hypertable
    create_hypertable(
        table_name="portfolio_performance",
        time_column="time",
        partitioning_column="portfolio_id",
        chunk_time_interval="1 day",
        number_partitions=2,
    )

    # Create performance indexes
    market_data_indexes = [
        {
            "name": "idx_market_data_symbol_time_desc",
            "columns": ["symbol", sa.text("time DESC")],
        },
        {
            "name": "idx_market_data_symbol_interval_time",
            "columns": ["symbol", "interval_type", sa.text("time DESC")],
        },
        {"name": "idx_market_data_volume", "columns": ["volume"]},
    ]

    technical_indicators_indexes = [
        {
            "name": "idx_technical_indicators_symbol_type_time",
            "columns": ["symbol", "indicator_type", sa.text("time DESC")],
        }
    ]

    signals_indexes = [
        {
            "name": "idx_signals_symbol_strength_time",
            "columns": ["symbol", "signal_strength", sa.text("time DESC")],
        },
        {
            "name": "idx_signals_type_time",
            "columns": ["signal_type", sa.text("time DESC")],
        },
    ]

    portfolio_performance_indexes = [
        {
            "name": "idx_portfolio_performance_portfolio_time",
            "columns": ["portfolio_id", sa.text("time DESC")],
        }
    ]

    # Create all indexes
    create_performance_indexes("market_data", market_data_indexes)
    create_performance_indexes("technical_indicators", technical_indicators_indexes)
    create_performance_indexes("signals", signals_indexes)
    create_performance_indexes("portfolio_performance", portfolio_performance_indexes)

    # Add compression policies (compress data older than 7 days)
    add_compression_policy("market_data", "7 days")
    add_compression_policy("technical_indicators", "7 days")
    add_compression_policy("signals", "30 days")
    add_compression_policy("portfolio_performance", "30 days")

    # Add retention policies (drop data older than 2 years for market_data)
    add_retention_policy("market_data", "2 years")
    add_retention_policy("technical_indicators", "1 year")
    add_retention_policy("signals", "1 year")
    add_retention_policy("portfolio_performance", "5 years")

    # Create continuous aggregates for real-time analytics

    # Daily market summary
    op.execute(
        text(
            """
    CREATE MATERIALIZED VIEW daily_market_summary
    WITH (timescaledb.continuous) AS
    SELECT time_bucket('1 day', time) AS day,
           symbol,
           first(open_price, time) AS open_price,
           max(high_price) AS high_price,
           min(low_price) AS low_price,
           last(close_price, time) AS close_price,
           sum(volume) AS total_volume,
           count(*) AS data_points
    FROM market_data
    GROUP BY day, symbol;
    """
        )
    )

    # Hourly portfolio performance summary
    op.execute(
        text(
            """
    CREATE MATERIALIZED VIEW hourly_portfolio_performance
    WITH (timescaledb.continuous) AS
    SELECT time_bucket('1 hour', time) AS hour,
           portfolio_id,
           avg(total_value) AS avg_value,
           max(total_value) AS max_value,
           min(total_value) AS min_value,
           last(total_return, time) AS last_return,
           stddev(daily_return) AS volatility
    FROM portfolio_performance
    GROUP BY hour, portfolio_id;
    """
        )
    )

    # Add refresh policies for continuous aggregates
    op.execute(
        text(
            """
    SELECT add_continuous_aggregate_policy('daily_market_summary',
        start_offset => INTERVAL '3 days',
        end_offset => INTERVAL '1 hour',
        schedule_interval => INTERVAL '1 hour');
    """
        )
    )

    op.execute(
        text(
            """
    SELECT add_continuous_aggregate_policy('hourly_portfolio_performance',
        start_offset => INTERVAL '1 day',
        end_offset => INTERVAL '1 hour',
        schedule_interval => INTERVAL '30 minutes');
    """
        )
    )


def downgrade() -> None:
    """Downgrade: Remove TimescaleDB optimizations."""

    # Drop continuous aggregates
    op.execute(text("DROP MATERIALIZED VIEW IF EXISTS daily_market_summary;"))
    op.execute(text("DROP MATERIALIZED VIEW IF EXISTS hourly_portfolio_performance;"))

    # Drop compression and retention policies
    compression_tables = [
        "market_data",
        "technical_indicators",
        "signals",
        "portfolio_performance",
    ]
    for table in compression_tables:
        op.execute(text(f"SELECT remove_compression_policy('{table}');"))
        op.execute(text(f"SELECT remove_retention_policy('{table}');"))

    # Drop performance indexes
    indexes_to_drop = [
        "idx_market_data_symbol_time_desc",
        "idx_market_data_symbol_interval_time",
        "idx_market_data_volume",
        "idx_technical_indicators_symbol_type_time",
        "idx_signals_symbol_strength_time",
        "idx_signals_type_time",
        "idx_portfolio_performance_portfolio_time",
    ]

    for index_name in indexes_to_drop:
        op.execute(text(f"DROP INDEX IF EXISTS {index_name};"))

    # Note: We don't drop hypertables as that would require dropping the tables entirely
    # In a real scenario, you might want to convert back to regular tables

    # Disable TimescaleDB extension (optional - might affect other databases)
    # op.execute(text("DROP EXTENSION IF EXISTS timescaledb;"))
