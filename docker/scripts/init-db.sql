#!/bin/bash
set -e

# Initialize Boursa Vision Database
echo "🚀 Initializing Boursa Vision Database..."

# Create TimescaleDB extension
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create TimescaleDB extension
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    
    -- Create extensions for advanced features
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pgcrypto";
    
    -- Create a test table to verify TimescaleDB is working
    CREATE TABLE IF NOT EXISTS market_data_test (
        time TIMESTAMPTZ NOT NULL,
        symbol TEXT NOT NULL,
        price NUMERIC(12,2) NOT NULL,
        volume BIGINT
    );
    
    -- Convert to hypertable (TimescaleDB feature)
    SELECT create_hypertable('market_data_test', 'time', if_not_exists => TRUE);
    
    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS market_data_test_symbol_time_idx 
    ON market_data_test (symbol, time DESC);
    
    -- Insert test data
    INSERT INTO market_data_test (time, symbol, price, volume) 
    VALUES (NOW(), 'TEST', 100.00, 1000)
    ON CONFLICT DO NOTHING;
    
    -- Grant permissions
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $POSTGRES_USER;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $POSTGRES_USER;
    
EOSQL

echo "✅ Database initialization completed successfully!"
echo "📊 TimescaleDB extension enabled"
echo "🔐 Extensions created: uuid-ossp, pgcrypto"
echo "📈 Test hypertable created: market_data_test"
