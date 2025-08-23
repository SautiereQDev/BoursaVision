"""Database migration to add data source tracking and improve data quality."""


def upgrade_market_data_archive():
    """Add data_source column to track data sources and improve debugging."""

    migration_sql = """
    -- Add data_source column if it doesn't exist
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'market_data_archive'
            AND column_name = 'data_source'
        ) THEN
            ALTER TABLE market_data_archive
            ADD COLUMN data_source TEXT NOT NULL DEFAULT 'yfinance';
        END IF;
    END $$;

    -- Create index on data_source for better performance
    CREATE INDEX IF NOT EXISTS idx_market_data_archive_source
    ON market_data_archive (data_source);

    -- Create composite index for better duplicate detection
    CREATE INDEX IF NOT EXISTS idx_market_data_archive_symbol_timestamp_source
    ON market_data_archive (symbol, timestamp, data_source);

    -- Add check constraint to ensure valid data sources
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.check_constraints
            WHERE constraint_name = 'chk_valid_data_source'
        ) THEN
            ALTER TABLE market_data_archive
            ADD CONSTRAINT chk_valid_data_source
            CHECK (data_source IN ('yfinance', 'alpha_vantage', 'manual', 'other'));
        END IF;
    END $$;
    """

    return migration_sql


def create_data_quality_views():
    """Create views for monitoring data quality."""

    views_sql = """
    -- View for detecting potential duplicate data
    CREATE OR REPLACE VIEW v_potential_duplicates AS
    SELECT
        symbol,
        timestamp,
        interval_type,
        COUNT(*) as record_count,
        COUNT(DISTINCT close_price) as distinct_prices,
        ARRAY_AGG(DISTINCT close_price ORDER BY close_price) as price_variants,
        ARRAY_AGG(DISTINCT data_source) as data_sources
    FROM market_data_archive
    GROUP BY symbol, timestamp, interval_type
    HAVING COUNT(*) > 1 OR COUNT(DISTINCT close_price) > 1;

    -- View for data quality metrics by symbol
    CREATE OR REPLACE VIEW v_data_quality_by_symbol AS
    SELECT
        symbol,
        COUNT(*) as total_records,
        COUNT(DISTINCT timestamp) as unique_timestamps,
        COUNT(DISTINCT data_source) as data_sources_count,
        MIN(timestamp) as oldest_record,
        MAX(timestamp) as newest_record,
        COUNT(CASE WHEN open_price IS NULL THEN 1 END) as missing_open,
        COUNT(CASE WHEN close_price IS NULL THEN 1 END) as missing_close,
        COUNT(CASE WHEN volume IS NULL THEN 1 END) as missing_volume
    FROM market_data_archive
    GROUP BY symbol
    ORDER BY total_records DESC;

    -- View for daily data quality summary
    CREATE OR REPLACE VIEW v_daily_data_quality AS
    SELECT
        DATE(timestamp) as date,
        COUNT(*) as total_records,
        COUNT(DISTINCT symbol) as symbols_count,
        COUNT(DISTINCT data_source) as sources_count,
        AVG(CASE WHEN open_price IS NOT NULL THEN 1.0 ELSE 0.0 END) as open_completeness,
        AVG(CASE WHEN close_price IS NOT NULL THEN 1.0 ELSE 0.0 END) as close_completeness,
        AVG(CASE WHEN volume IS NOT NULL THEN 1.0 ELSE 0.0 END) as volume_completeness
    FROM market_data_archive
    GROUP BY DATE(timestamp)
    ORDER BY date DESC;
    """

    return views_sql


def main_migration():
    """Execute the complete migration."""
    return upgrade_market_data_archive() + "\n\n" + create_data_quality_views()


if __name__ == "__main__":
    print("📊 Database Migration for Enhanced Data Quality")
    print("=" * 50)
    print(main_migration())
