"""Add performance indexes for trading queries

Revision ID: 002_performance_indexes
Revises: 001_create_hypertables
Create Date: 2025-08-11 12:30:00.000000

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "002_performance_indexes"
down_revision = "001_create_hypertables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create performance indexes for optimal query performance."""

    # User table indexes
    op.create_index("idx_users_email", "users", ["email"], unique=True)
    op.create_index("idx_users_username", "users", ["username"], unique=True)
    op.create_index("idx_users_active", "users", ["is_active"])

    # Portfolio table indexes
    op.create_index("idx_portfolios_user_id", "portfolios", ["user_id"])
    op.create_index(
        "idx_portfolios_user_active", "portfolios", ["user_id", "is_active"]
    )

    # Position table indexes
    op.create_index("idx_positions_portfolio_id", "positions", ["portfolio_id"])
    op.create_index("idx_positions_instrument_id", "positions", ["instrument_id"])
    op.create_index("idx_positions_symbol", "positions", ["symbol"])
    op.create_index(
        "idx_positions_portfolio_symbol", "positions", ["portfolio_id", "symbol"]
    )

    # Transaction table indexes
    op.create_index("idx_transactions_portfolio_id", "transactions", ["portfolio_id"])
    op.create_index("idx_transactions_instrument_id", "transactions", ["instrument_id"])
    op.create_index("idx_transactions_symbol", "transactions", ["symbol"])
    op.create_index("idx_transactions_type", "transactions", ["transaction_type"])
    op.create_index("idx_transactions_date", "transactions", ["transaction_date"])
    op.create_index(
        "idx_transactions_portfolio_date",
        "transactions",
        ["portfolio_id", "transaction_date"],
    )

    # Instrument table indexes
    op.create_index("idx_instruments_symbol", "instruments", ["symbol"], unique=True)
    op.create_index("idx_instruments_exchange", "instruments", ["exchange"])
    op.create_index("idx_instruments_sector", "instruments", ["sector"])
    op.create_index("idx_instruments_industry", "instruments", ["industry"])
    op.create_index("idx_instruments_active", "instruments", ["is_active"])
    op.create_index("idx_instruments_type", "instruments", ["instrument_type"])

    # Fundamental data indexes
    op.create_index(
        "idx_fundamental_data_instrument_id", "fundamental_data", ["instrument_id"]
    )
    op.create_index("idx_fundamental_data_symbol", "fundamental_data", ["symbol"])
    op.create_index(
        "idx_fundamental_data_period", "fundamental_data", ["period_end_date"]
    )
    op.create_index(
        "idx_fundamental_data_symbol_period",
        "fundamental_data",
        ["symbol", "period_end_date"],
    )

    # Alert table indexes
    op.create_index("idx_alerts_user_id", "alerts", ["user_id"])
    op.create_index("idx_alerts_portfolio_id", "alerts", ["portfolio_id"])
    op.create_index("idx_alerts_symbol", "alerts", ["symbol"])
    op.create_index("idx_alerts_active", "alerts", ["is_active"])
    op.create_index("idx_alerts_type", "alerts", ["alert_type"])

    # Notification table indexes
    op.create_index("idx_notifications_user_id", "notifications", ["user_id"])
    op.create_index("idx_notifications_read", "notifications", ["is_read"])
    op.create_index("idx_notifications_created", "notifications", ["created_at"])

    # System table indexes
    op.create_index("idx_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])
    op.create_index("idx_audit_logs_timestamp", "audit_logs", ["timestamp"])

    # Composite indexes for common query patterns
    op.create_index(
        "idx_market_data_symbol_interval_time",
        "market_data",
        ["symbol", "interval_type", sa.text("time DESC")],
    )

    op.create_index(
        "idx_technical_indicators_symbol_name_time",
        "technical_indicators",
        ["symbol", "indicator_name", sa.text("time DESC")],
    )

    op.create_index(
        "idx_signals_symbol_type_time",
        "signals",
        ["symbol", "signal_type", sa.text("time DESC")],
    )

    # Partial indexes for active records only
    op.create_index(
        "idx_portfolios_active_only",
        "portfolios",
        ["user_id", "name"],
        postgresql_where=sa.text("is_active = true"),
    )

    op.create_index(
        "idx_instruments_active_only",
        "instruments",
        ["exchange", "sector"],
        postgresql_where=sa.text("is_active = true"),
    )

    # Covering indexes for read-heavy queries
    op.create_index(
        "idx_positions_portfolio_covering",
        "positions",
        ["portfolio_id"],
        postgresql_include=["symbol", "quantity", "average_cost", "current_price"],
    )


def downgrade() -> None:
    """Remove performance indexes."""

    # Drop all indexes created in upgrade
    indexes_to_drop = [
        ("users", "idx_users_email"),
        ("users", "idx_users_username"),
        ("users", "idx_users_active"),
        ("portfolios", "idx_portfolios_user_id"),
        ("portfolios", "idx_portfolios_user_active"),
        ("portfolios", "idx_portfolios_active_only"),
        ("positions", "idx_positions_portfolio_id"),
        ("positions", "idx_positions_instrument_id"),
        ("positions", "idx_positions_symbol"),
        ("positions", "idx_positions_portfolio_symbol"),
        ("positions", "idx_positions_portfolio_covering"),
        ("transactions", "idx_transactions_portfolio_id"),
        ("transactions", "idx_transactions_instrument_id"),
        ("transactions", "idx_transactions_symbol"),
        ("transactions", "idx_transactions_type"),
        ("transactions", "idx_transactions_date"),
        ("transactions", "idx_transactions_portfolio_date"),
        ("instruments", "idx_instruments_symbol"),
        ("instruments", "idx_instruments_exchange"),
        ("instruments", "idx_instruments_sector"),
        ("instruments", "idx_instruments_industry"),
        ("instruments", "idx_instruments_active"),
        ("instruments", "idx_instruments_type"),
        ("instruments", "idx_instruments_active_only"),
        ("fundamental_data", "idx_fundamental_data_instrument_id"),
        ("fundamental_data", "idx_fundamental_data_symbol"),
        ("fundamental_data", "idx_fundamental_data_period"),
        ("fundamental_data", "idx_fundamental_data_symbol_period"),
        ("alerts", "idx_alerts_user_id"),
        ("alerts", "idx_alerts_portfolio_id"),
        ("alerts", "idx_alerts_symbol"),
        ("alerts", "idx_alerts_active"),
        ("alerts", "idx_alerts_type"),
        ("notifications", "idx_notifications_user_id"),
        ("notifications", "idx_notifications_read"),
        ("notifications", "idx_notifications_created"),
        ("audit_logs", "idx_audit_logs_user_id"),
        ("audit_logs", "idx_audit_logs_action"),
        ("audit_logs", "idx_audit_logs_timestamp"),
        ("market_data", "idx_market_data_symbol_interval_time"),
        ("technical_indicators", "idx_technical_indicators_symbol_name_time"),
        ("signals", "idx_signals_symbol_type_time"),
    ]

    for table, index in indexes_to_drop:
        op.drop_index(index, table)
