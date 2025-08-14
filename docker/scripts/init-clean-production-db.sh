#!/bin/bash

# Production database initialization script for Boursa Vision
# This script ensures only production tables are created

set -e

echo "🏛️  Initializing Boursa Vision production database..."

# Ensure TimescaleDB extension is enabled
echo "⚡ Enabling TimescaleDB extension..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
EOSQL

echo "✅ TimescaleDB extension enabled!"

# Create market_data_archive table directly (production-ready)
echo "📊 Creating market_data_archive table..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create market_data_archive table
    CREATE TABLE IF NOT EXISTS market_data_archive (
        id SERIAL,
        symbol TEXT NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        open_price DECIMAL(20,8),
        high_price DECIMAL(20,8),
        low_price DECIMAL(20,8),
        close_price DECIMAL(20,8),
        volume BIGINT,
        interval_type TEXT NOT NULL DEFAULT '1d',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        PRIMARY KEY (id, timestamp),
        CONSTRAINT uix_symbol_timestamp_interval UNIQUE (symbol, timestamp, interval_type)
    );

    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_market_data_archive_symbol ON market_data_archive (symbol);
    CREATE INDEX IF NOT EXISTS idx_market_data_archive_timestamp ON market_data_archive (timestamp);
    CREATE INDEX IF NOT EXISTS idx_market_data_archive_symbol_timestamp ON market_data_archive (symbol, timestamp);

    -- Convert to TimescaleDB hypertable
    SELECT create_hypertable(
        'market_data_archive', 
        'timestamp',
        chunk_time_interval => INTERVAL '1 day',
        if_not_exists => TRUE
    );

    -- Configure compression for old data
    ALTER TABLE market_data_archive SET (
        timescaledb.compress,
        timescaledb.compress_segmentby = 'symbol',
        timescaledb.compress_orderby = 'timestamp DESC'
    );

    -- Add compression policy (compress data older than 7 days)
    SELECT add_compression_policy('market_data_archive', INTERVAL '7 days');

    -- Grant permissions
    GRANT ALL PRIVILEGES ON TABLE market_data_archive TO $POSTGRES_USER;
    GRANT USAGE, SELECT ON SEQUENCE market_data_archive_id_seq TO $POSTGRES_USER;
EOSQL

echo "✅ market_data_archive table created with TimescaleDB optimization!"

# Remove any test tables if they exist
echo "🧹 Cleaning any test tables..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DROP TABLE IF EXISTS market_data_test CASCADE;
EOSQL

# Show final table structure
echo "📋 Final database structure:"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -c "\dt"

echo "🎉 Production database initialization completed!"
