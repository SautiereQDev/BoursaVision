"""
Alembic migration utilities with TimescaleDB support.
"""

from sqlalchemy import text

from alembic import op


def create_hypertable(
    table_name: str,
    time_column: str,
    partitioning_column: str = None,
    chunk_time_interval: str = "1 day",
    number_partitions: int = 4,
):
    """
    Create a TimescaleDB hypertable.

    Args:
        table_name: Name of the table to convert to hypertable
        time_column: Name of the time column
        partitioning_column: Optional partitioning column for space partitioning
        chunk_time_interval: Time interval for chunks (e.g., "1 day", "1 hour")
        number_partitions: Number of space partitions (if partitioning_column is used)
    """
    if partitioning_column:
        sql = f"""
        SELECT create_hypertable(
            '{table_name}', 
            '{time_column}',
            partitioning_column => '{partitioning_column}',
            number_partitions => {number_partitions},
            chunk_time_interval => INTERVAL '{chunk_time_interval}'
        );
        """
    else:
        sql = f"""
        SELECT create_hypertable(
            '{table_name}', 
            '{time_column}',
            chunk_time_interval => INTERVAL '{chunk_time_interval}'
        );
        """

    op.execute(text(sql))


def add_compression_policy(table_name: str, compress_after: str):
    """
    Add compression policy to a hypertable.

    Args:
        table_name: Name of the hypertable
        compress_after: Interval after which to compress (e.g., "7 days")
    """
    sql = f"SELECT add_compression_policy('{table_name}', INTERVAL '{compress_after}');"
    op.execute(text(sql))


def add_retention_policy(table_name: str, drop_after: str):
    """
    Add retention policy to automatically drop old data.

    Args:
        table_name: Name of the hypertable
        drop_after: Interval after which to drop chunks (e.g., "1 year")
    """
    sql = f"SELECT add_retention_policy('{table_name}', INTERVAL '{drop_after}');"
    op.execute(text(sql))


def create_continuous_aggregate(
    view_name: str,
    table_name: str,
    time_column: str,
    bucket_width: str,
    select_query: str,
):
    """
    Create a continuous aggregate for real-time analytics.

    Args:
        view_name: Name of the continuous aggregate view
        table_name: Source hypertable name
        time_column: Time column for bucketing
        bucket_width: Time bucket width (e.g., "1 hour", "1 day")
        select_query: Custom SELECT query for the aggregate
    """
    sql = f"""
    CREATE MATERIALIZED VIEW {view_name}
    WITH (timescaledb.continuous) AS
    SELECT time_bucket('{bucket_width}', {time_column}) AS bucket,
           {select_query}
    FROM {table_name}
    GROUP BY bucket;
    """
    op.execute(text(sql))


def add_refresh_policy(
    view_name: str,
    start_offset: str = "1 hour",
    end_offset: str = "1 minute",
    schedule_interval: str = "1 hour",
):
    """
    Add refresh policy for continuous aggregate.

    Args:
        view_name: Name of the continuous aggregate view
        start_offset: How far back to refresh from current time
        end_offset: How close to current time to refresh
        schedule_interval: How often to refresh
    """
    sql = f"""
    SELECT add_continuous_aggregate_policy('{view_name}',
        start_offset => INTERVAL '{start_offset}',
        end_offset => INTERVAL '{end_offset}',
        schedule_interval => INTERVAL '{schedule_interval}');
    """
    op.execute(text(sql))


def create_performance_indexes(table_name: str, indexes: list):
    """
    Create performance indexes for time-series queries.

    Args:
        table_name: Name of the table
        indexes: List of index definitions
    """
    for index in indexes:
        op.create_index(
            index["name"],
            table_name,
            index["columns"],
            postgresql_concurrently=True,
            if_not_exists=True,
        )
