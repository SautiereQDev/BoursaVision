#!/bin/bash

# Clean and initialize production database for Boursa Vision
# This script ensures the database only contains production tables

set -e

echo "🧹 Cleaning and initializing Boursa Vision database..."

# Database connection parameters
DB_HOST=${POSTGRES_HOST:-postgres}
DB_PORT=${POSTGRES_PORT:-5432}
DB_NAME=${POSTGRES_DB:-boursa_vision}
DB_USER=${POSTGRES_USER:-boursa_user}

echo "📋 Database info:"
echo "  Host: $DB_HOST"
echo "  Port: $DB_PORT"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"; do
  sleep 2
done

echo "✅ Database is ready!"

# Drop all existing tables (clean slate)
echo "🗑️  Dropping all existing tables..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" << 'EOF'
-- Drop all tables and sequences
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO boursa_user;
GRANT ALL ON SCHEMA public TO public;

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
EOF

echo "✅ Database cleaned successfully!"

# Initialize Alembic version table
echo "🏗️  Initializing Alembic..."
export DATABASE_URL="postgresql://$DB_USER:$POSTGRES_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"

# Run migrations
echo "📦 Running database migrations..."
poetry run alembic upgrade head

echo "✅ Database initialization completed!"

# Verify tables
echo "📊 Verifying created tables..."
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\dt"

echo "🎉 Database setup completed successfully!"
