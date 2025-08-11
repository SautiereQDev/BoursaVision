"""Complete relationships and add missing foreign keys

Revision ID: 003_complete_relationships
Revises: 002_performance_indexes
Create Date: 2025-08-11 15:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "003_complete_relationships"
down_revision = "002_performance_indexes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing foreign key constraints and complete relationships."""

    # Add missing foreign key for positions -> instruments
    # This ensures data integrity between positions and instruments
    op.execute("""
        ALTER TABLE positions 
        ADD CONSTRAINT fk_positions_instrument_id 
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) 
        ON DELETE RESTRICT;
    """)

    # Add missing foreign key for positions -> portfolios
    op.execute("""
        ALTER TABLE positions 
        ADD CONSTRAINT fk_positions_portfolio_id 
        FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) 
        ON DELETE CASCADE;
    """)

    # Add missing foreign key for transactions -> instruments
    op.execute("""
        ALTER TABLE transactions 
        ADD CONSTRAINT fk_transactions_instrument_id 
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) 
        ON DELETE RESTRICT;
    """)

    # Add missing foreign key for transactions -> portfolios
    op.execute("""
        ALTER TABLE transactions 
        ADD CONSTRAINT fk_transactions_portfolio_id 
        FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) 
        ON DELETE CASCADE;
    """)

    # Add missing foreign key for fundamental_data -> instruments
    op.execute("""
        ALTER TABLE fundamental_data 
        ADD CONSTRAINT fk_fundamental_data_instrument_id 
        FOREIGN KEY (instrument_id) REFERENCES instruments(id) 
        ON DELETE CASCADE;
    """)

    # Add missing foreign key for alerts -> users
    op.execute("""
        ALTER TABLE alerts 
        ADD CONSTRAINT fk_alerts_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE;
    """)

    # Add missing foreign key for alerts -> portfolios (optional)
    op.execute("""
        ALTER TABLE alerts 
        ADD CONSTRAINT fk_alerts_portfolio_id 
        FOREIGN KEY (portfolio_id) REFERENCES portfolios(id) 
        ON DELETE SET NULL;
    """)

    # Add missing foreign key for user_sessions -> users
    op.execute("""
        ALTER TABLE user_sessions 
        ADD CONSTRAINT fk_user_sessions_user_id 
        FOREIGN KEY (user_id) REFERENCES users(id) 
        ON DELETE CASCADE;
    """)

    # Add missing foreign key for notifications -> alerts
    op.execute("""
        ALTER TABLE notifications 
        ADD CONSTRAINT fk_notifications_alert_id 
        FOREIGN KEY (alert_id) REFERENCES alerts(id) 
        ON DELETE CASCADE;
    """)

    # Add some additional performance indexes for relationships
    
    # Composite index for position lookups by portfolio and symbol
    op.create_index(
        "idx_positions_portfolio_symbol_composite",
        "positions",
        ["portfolio_id", "symbol", "is_active"],
    )

    # Index for transaction history queries
    op.create_index(
        "idx_transactions_portfolio_date_type",
        "transactions",
        ["portfolio_id", "executed_at", "transaction_type"],
    )

    # Index for alert queries by user and status
    op.create_index(
        "idx_alerts_user_active_triggered",
        "alerts",
        ["user_id", "is_active", "is_triggered"],
    )

    # Index for fundamental data by symbol and period
    op.create_index(
        "idx_fundamental_data_symbol_period_desc",
        "fundamental_data",
        ["symbol", sa.text("period_end_date DESC")],
    )

    # Index for user sessions by user and activity
    op.create_index(
        "idx_user_sessions_user_active",
        "user_sessions",
        ["user_id", "is_active"],
    )

    # Add check constraints for data integrity

    # Ensure positive quantities in positions
    op.execute("""
        ALTER TABLE positions 
        ADD CONSTRAINT check_positions_quantity_positive 
        CHECK (quantity >= 0);
    """)

    # Ensure positive amounts in transactions (except for sells which can be negative)
    op.execute("""
        ALTER TABLE transactions 
        ADD CONSTRAINT check_transactions_amount_reasonable 
        CHECK (amount != 0);
    """)

    # Ensure reasonable price ranges
    op.execute("""
        ALTER TABLE transactions 
        ADD CONSTRAINT check_transactions_price_positive 
        CHECK (price > 0);
    """)

    # Ensure portfolio cash values are reasonable
    op.execute("""
        ALTER TABLE portfolios 
        ADD CONSTRAINT check_portfolios_cash_reasonable 
        CHECK (current_cash >= 0 AND initial_cash >= 0);
    """)


def downgrade() -> None:
    """Remove the foreign key constraints and indexes added in upgrade."""

    # Remove check constraints
    op.execute("ALTER TABLE portfolios DROP CONSTRAINT IF EXISTS check_portfolios_cash_reasonable;")
    op.execute("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS check_transactions_price_positive;")
    op.execute("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS check_transactions_amount_reasonable;")
    op.execute("ALTER TABLE positions DROP CONSTRAINT IF EXISTS check_positions_quantity_positive;")

    # Remove performance indexes
    op.drop_index("idx_user_sessions_user_active", "user_sessions")
    op.drop_index("idx_fundamental_data_symbol_period_desc", "fundamental_data")
    op.drop_index("idx_alerts_user_active_triggered", "alerts")
    op.drop_index("idx_transactions_portfolio_date_type", "transactions")
    op.drop_index("idx_positions_portfolio_symbol_composite", "positions")

    # Remove foreign key constraints
    op.execute("ALTER TABLE notifications DROP CONSTRAINT IF EXISTS fk_notifications_alert_id;")
    op.execute("ALTER TABLE user_sessions DROP CONSTRAINT IF EXISTS fk_user_sessions_user_id;")
    op.execute("ALTER TABLE alerts DROP CONSTRAINT IF EXISTS fk_alerts_portfolio_id;")
    op.execute("ALTER TABLE alerts DROP CONSTRAINT IF EXISTS fk_alerts_user_id;")
    op.execute("ALTER TABLE fundamental_data DROP CONSTRAINT IF EXISTS fk_fundamental_data_instrument_id;")
    op.execute("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS fk_transactions_portfolio_id;")
    op.execute("ALTER TABLE transactions DROP CONSTRAINT IF EXISTS fk_transactions_instrument_id;")
    op.execute("ALTER TABLE positions DROP CONSTRAINT IF EXISTS fk_positions_portfolio_id;")
    op.execute("ALTER TABLE positions DROP CONSTRAINT IF EXISTS fk_positions_instrument_id;")
