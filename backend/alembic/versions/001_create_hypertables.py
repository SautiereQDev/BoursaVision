"""Create TimescaleDB hypertables

Revision ID: 001_create_hypertables
Revises: 001_timescaledb_setup
Create Date: 2025-08-11 12:00:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "001_create_hypertables"
down_revision = "001_timescaledb_setup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create TimescaleDB hypertables for time-series data."""

    # Ensure TimescaleDB extension is enabled
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")

    # Create market_data hypertable
    op.execute(
        """
        SELECT create_hypertable(
            'market_data', 
            'time',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
    """
    )

    # Create technical_indicators hypertable
    op.execute(
        """
        SELECT create_hypertable(
            'technical_indicators', 
            'time',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
    """
    )

    # Create signals hypertable
    op.execute(
        """
        SELECT create_hypertable(
            'signals', 
            'time',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
    """
    )

    # Create portfolio_performance hypertable
    op.execute(
        """
        SELECT create_hypertable(
            'portfolio_performance', 
            'time',
            chunk_time_interval => INTERVAL '1 day',
            if_not_exists => TRUE
        );
    """
    )

    # Create performance indexes for optimal querying

    # Market data indexes
    op.create_index(
        "idx_market_data_symbol_time_desc",
        "market_data",
        ["symbol", sa.text("time DESC")],
        postgresql_where=sa.text("interval_type = '1d'"),
    )

    op.create_index(
        "idx_market_data_time_symbol",
        "market_data",
        ["time", "symbol"],
        postgresql_using="btree",
    )

    # Technical indicators indexes
    op.create_index(
        "idx_technical_indicators_symbol_time",
        "technical_indicators",
        ["symbol", "time", "indicator_name"],
    )

    # Signals indexes
    op.create_index(
        "idx_signals_symbol_time", "signals", ["symbol", "time", "signal_type"]
    )

    # Portfolio performance indexes
    op.create_index(
        "idx_portfolio_performance_time",
        "portfolio_performance",
        ["portfolio_id", "time"],
    )

    # Create continuous aggregates for better performance

    # Hourly market data aggregation
    op.execute(
        """
        CREATE MATERIALIZED VIEW market_data_hourly
        WITH (timescaledb.continuous) AS
        SELECT 
            time_bucket('1 hour', time) AS hour,
            symbol,
            interval_type,
            first(open_price, time) AS open_price,
            max(high_price) AS high_price,
            min(low_price) AS low_price,
            last(close_price, time) AS close_price,
            sum(volume) AS volume,
            count(*) AS data_points
        FROM market_data
        WHERE interval_type IN ('1m', '5m', '15m')
        GROUP BY hour, symbol, interval_type
        WITH NO DATA;
    """
    )

    # Daily portfolio performance aggregation
    op.execute(
        """
        CREATE MATERIALIZED VIEW portfolio_performance_daily
        WITH (timescaledb.continuous) AS
        SELECT 
            time_bucket('1 day', time) AS day,
            portfolio_id,
            last(total_value, time) AS total_value,
            last(cash_value, time) AS cash_value,
            last(invested_value, time) AS invested_value,
            last(daily_return, time) AS daily_return,
            avg(volatility) AS avg_volatility,
            max(sharpe_ratio) AS max_sharpe_ratio
        FROM portfolio_performance
        GROUP BY day, portfolio_id
        WITH NO DATA;
    """
    )

    # Create compression policies for data retention
    op.execute(
        """
        SELECT add_compression_policy('market_data', INTERVAL '7 days');
    """
    )

    op.execute(
        """
        SELECT add_compression_policy('technical_indicators', INTERVAL '7 days');
    """
    )

    op.execute(
        """
        SELECT add_compression_policy('portfolio_performance', INTERVAL '7 days');
    """
    )

    # Create retention policies
    op.execute(
        """
        SELECT add_retention_policy('market_data', INTERVAL '2 years');
    """
    )

    op.execute(
        """
        SELECT add_retention_policy('technical_indicators', INTERVAL '1 year');
    """
    )


def downgrade() -> None:
    """Remove TimescaleDB hypertables and related objects."""

    # Drop continuous aggregates
    op.execute("DROP MATERIALIZED VIEW IF EXISTS market_data_hourly CASCADE;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS portfolio_performance_daily CASCADE;")

    # Drop compression and retention policies
    op.execute("SELECT remove_compression_policy('market_data', if_exists => true);")
    op.execute(
        "SELECT remove_compression_policy('technical_indicators', if_exists => true);"
    )
    op.execute(
        "SELECT remove_compression_policy('portfolio_performance', if_exists => true);"
    )

    op.execute("SELECT remove_retention_policy('market_data', if_exists => true);")
    op.execute(
        "SELECT remove_retention_policy('technical_indicators', if_exists => true);"
    )

    # Drop indexes
    op.drop_index("idx_market_data_symbol_time_desc", "market_data")
    op.drop_index("idx_market_data_time_symbol", "market_data")
    op.drop_index("idx_technical_indicators_symbol_time", "technical_indicators")
    op.drop_index("idx_signals_symbol_time", "signals")
    op.drop_index("idx_portfolio_performance_time", "portfolio_performance")

    # Note: Cannot easily drop hypertables, would require dropping entire tables
