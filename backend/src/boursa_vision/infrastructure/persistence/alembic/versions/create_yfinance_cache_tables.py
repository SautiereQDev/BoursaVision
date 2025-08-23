"""Cache intelligent pour données YFinance

Revision ID: create_yfinance_cache_tables
Revises: 0dcd4a7801e8_create_all_base_tables
Create Date: 2025-01-13 10:00:00.000000

Crée les tables optimisées pour le cache intelligent des données YFinance
avec gestion de la précision temporelle et TimescaleDB.
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision = "create_yfinance_cache_tables"
down_revision = "0dcd4a7801e8_create_all_base_tables"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Création des tables de cache YFinance optimisées"""

    # Table principale de cache des données de marché
    op.create_table(
        "market_data_cache",
        sa.Column("time", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("interval_type", sa.String(length=5), nullable=False),
        sa.Column("open_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("high_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("low_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("close_price", sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column("adjusted_close", sa.Numeric(precision=20, scale=8), nullable=True),
        sa.Column("volume", sa.BigInteger(), nullable=True, default=0),
        sa.Column(
            "data_source", sa.String(length=20), nullable=False, default="yfinance"
        ),
        sa.Column("precision_level", sa.String(length=15), nullable=False),
        sa.Column("cache_priority", sa.Integer(), nullable=False, default=5),
        sa.Column("access_count", sa.Integer(), nullable=False, default=0),
        sa.Column("last_accessed", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("cache_ttl_seconds", sa.Integer(), nullable=False, default=3600),
        sa.Column("yfinance_period", sa.String(length=10), nullable=True),
        sa.Column("yfinance_interval", sa.String(length=5), nullable=True),
        sa.Column(
            "price_change_percent", sa.Numeric(precision=8, scale=4), nullable=True
        ),
        sa.Column("volume_sma_20", sa.BigInteger(), nullable=True),
        sa.Column(
            "is_significant_movement", sa.Boolean(), nullable=False, default=False
        ),
        sa.Column("fetched_at", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("data_age_hours", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        # Clé primaire composite pour TimescaleDB
        sa.PrimaryKeyConstraint("time", "symbol", "interval_type"),
        # Contraintes de validation
        sa.CheckConstraint(
            "high_price >= open_price AND high_price >= close_price",
            name="check_high_price_valid",
        ),
        sa.CheckConstraint(
            "low_price <= open_price AND low_price <= close_price",
            name="check_low_price_valid",
        ),
        sa.CheckConstraint("volume >= 0", name="check_volume_positive"),
        sa.CheckConstraint(
            "precision_level IN ('ultra_high', 'high', 'medium', 'low', 'very_low')",
            name="check_precision_level",
        ),
        sa.CheckConstraint(
            "data_source IN ('yfinance', 'yahoo_finance', 'alpha_vantage', 'internal_cache')",
            name="check_data_source",
        ),
        sa.CheckConstraint(
            "cache_priority >= 1 AND cache_priority <= 10", name="check_cache_priority"
        ),
    )

    # Index optimisés pour TimescaleDB
    op.create_index(
        "idx_market_data_cache_symbol_time", "market_data_cache", ["symbol", "time"]
    )
    op.create_index(
        "idx_market_data_cache_time_desc", "market_data_cache", [sa.text("time DESC")]
    )
    op.create_index(
        "idx_market_data_cache_precision",
        "market_data_cache",
        ["precision_level", "time"],
    )
    op.create_index(
        "idx_market_data_cache_access", "market_data_cache", ["last_accessed"]
    )
    op.create_index(
        "idx_market_data_cache_significant",
        "market_data_cache",
        ["is_significant_movement"],
        postgresql_where=sa.text("is_significant_movement = true"),
    )

    # Table des métriques de timeline
    op.create_table(
        "timeline_metrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("total_points", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "data_coverage_percent",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            default=0,
        ),
        sa.Column("gaps_count", sa.Integer(), nullable=False, default=0),
        sa.Column("significant_gaps_count", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "precision_distribution",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("oldest_point", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("newest_point", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column(
            "data_quality_score",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            default=0,
        ),
        sa.Column(
            "average_access_frequency",
            sa.Numeric(precision=8, scale=2),
            nullable=False,
            default=0,
        ),
        sa.Column(
            "cache_hit_rate",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            default=0,
        ),
        sa.Column(
            "last_calculated", postgresql.TIMESTAMP(timezone=True), nullable=False
        ),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("symbol", name="uq_timeline_metrics_symbol"),
    )

    op.create_index("idx_timeline_metrics_symbol", "timeline_metrics", ["symbol"])
    op.create_index(
        "idx_timeline_metrics_quality", "timeline_metrics", ["data_quality_score"]
    )
    op.create_index(
        "idx_timeline_metrics_last_calc", "timeline_metrics", ["last_calculated"]
    )

    # Table des statistiques de cache
    op.create_table(
        "cache_statistics",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "measurement_start", postgresql.TIMESTAMP(timezone=True), nullable=False
        ),
        sa.Column(
            "measurement_end", postgresql.TIMESTAMP(timezone=True), nullable=False
        ),
        sa.Column("total_requests", sa.BigInteger(), nullable=False, default=0),
        sa.Column("cache_hits", sa.BigInteger(), nullable=False, default=0),
        sa.Column("cache_misses", sa.BigInteger(), nullable=False, default=0),
        sa.Column(
            "cache_hit_rate",
            sa.Numeric(precision=5, scale=2),
            nullable=False,
            default=0,
        ),
        sa.Column("yfinance_requests", sa.Integer(), nullable=False, default=0),
        sa.Column("yfinance_errors", sa.Integer(), nullable=False, default=0),
        sa.Column(
            "average_response_time_ms", sa.Numeric(precision=8, scale=2), nullable=True
        ),
        sa.Column("db_reads", sa.Integer(), nullable=False, default=0),
        sa.Column("db_writes", sa.Integer(), nullable=False, default=0),
        sa.Column("db_deletes", sa.Integer(), nullable=False, default=0),
        sa.Column("memory_usage_mb", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("timelines_in_memory", sa.Integer(), nullable=False, default=0),
        sa.Column("cache_entries_count", sa.Integer(), nullable=False, default=0),
        sa.Column("evictions_lru", sa.Integer(), nullable=False, default=0),
        sa.Column("evictions_expired", sa.Integer(), nullable=False, default=0),
        sa.Column("cleanup_operations", sa.Integer(), nullable=False, default=0),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "idx_cache_stats_period",
        "cache_statistics",
        ["measurement_start", "measurement_end"],
    )
    op.create_index("idx_cache_stats_hit_rate", "cache_statistics", ["cache_hit_rate"])

    # Table des gaps de données
    op.create_table(
        "data_gaps",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("gap_start", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("gap_end", postgresql.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("gap_duration_minutes", sa.Integer(), nullable=False),
        sa.Column("expected_interval", sa.String(length=5), nullable=False),
        sa.Column("interval_type", sa.String(length=5), nullable=False),
        sa.Column("is_significant", sa.Boolean(), nullable=False, default=False),
        sa.Column("gap_reason", sa.String(length=100), nullable=True),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, default=False),
        sa.Column("resolution_method", sa.String(length=50), nullable=True),
        sa.Column("resolved_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_data_gaps_symbol_time", "data_gaps", ["symbol", "gap_start"])
    op.create_index("idx_data_gaps_significant", "data_gaps", ["is_significant"])
    op.create_index(
        "idx_data_gaps_unresolved",
        "data_gaps",
        ["is_resolved"],
        postgresql_where=sa.text("is_resolved = false"),
    )

    # Table des politiques de précision
    op.create_table(
        "precision_policies",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("symbol_pattern", sa.String(length=50), nullable=True),
        sa.Column(
            "interval_types", postgresql.JSONB(astext_type=sa.Text()), nullable=True
        ),
        sa.Column("market_cap_min", sa.BigInteger(), nullable=True),
        sa.Column("volume_min", sa.BigInteger(), nullable=True),
        sa.Column("ultra_high_ttl_hours", sa.Integer(), nullable=False, default=1),
        sa.Column("high_ttl_hours", sa.Integer(), nullable=False, default=24),
        sa.Column("medium_ttl_hours", sa.Integer(), nullable=False, default=168),
        sa.Column("low_ttl_hours", sa.Integer(), nullable=False, default=720),
        sa.Column("very_low_ttl_hours", sa.Integer(), nullable=False, default=8760),
        sa.Column(
            "cache_priority_multiplier",
            sa.Numeric(precision=3, scale=2),
            nullable=False,
            default=1.0,
        ),
        sa.Column(
            "enable_predictive_caching", sa.Boolean(), nullable=False, default=False
        ),
        sa.Column(
            "max_cache_points_per_symbol", sa.Integer(), nullable=False, default=10000
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, default=True),
        sa.Column("priority", sa.Integer(), nullable=False, default=100),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("policy_name"),
    )

    op.create_index(
        "idx_precision_policies_active", "precision_policies", ["is_active"]
    )
    op.create_index(
        "idx_precision_policies_priority", "precision_policies", ["priority"]
    )

    # Configuration TimescaleDB - Création des hypertables
    # Ces commandes doivent être exécutées manuellement ou via un script post-migration
    op.execute(
        """
        -- Activation de TimescaleDB si pas déjà fait
        -- CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
        
        -- Conversion de la table principale en hypertable
        -- SELECT create_hypertable('market_data_cache', 'time', 
        --                         chunk_time_interval => INTERVAL '1 day',
        --                         partitioning_column => 'symbol',
        --                         number_partitions => 4);
        
        -- Configuration des politiques de rétention
        -- SELECT add_retention_policy('market_data_cache', INTERVAL '2 years');
        
        -- Configuration de la compression automatique
        -- ALTER TABLE market_data_cache SET (
        --     timescaledb.compress,
        --     timescaledb.compress_segmentby = 'symbol,interval_type',
        --     timescaledb.compress_orderby = 'time DESC'
        -- );
        
        -- SELECT add_compression_policy('market_data_cache', INTERVAL '7 days');
        
        -- Politiques par défaut
        INSERT INTO precision_policies (
            id, policy_name, description, is_active, priority,
            ultra_high_ttl_hours, high_ttl_hours, medium_ttl_hours, 
            low_ttl_hours, very_low_ttl_hours
        ) VALUES (
            gen_random_uuid(),
            'default_policy',
            'Politique par défaut pour tous les symboles',
            true,
            100,
            1,    -- ultra_high: 1 heure
            24,   -- high: 1 jour  
            168,  -- medium: 1 semaine
            720,  -- low: 1 mois
            8760  -- very_low: 1 an
        );
        
        INSERT INTO precision_policies (
            id, policy_name, description, symbol_pattern, is_active, priority,
            ultra_high_ttl_hours, high_ttl_hours, medium_ttl_hours,
            low_ttl_hours, very_low_ttl_hours, cache_priority_multiplier
        ) VALUES (
            gen_random_uuid(),
            'major_stocks_policy',
            'Politique pour les grandes capitalisations',
            '^(AAPL|MSFT|GOOGL|AMZN|TSLA|META|NVDA|BRK-B|UNH|JNJ)$',
            true,
            10,   -- Priorité élevée
            0.25, -- ultra_high: 15 minutes
            4,    -- high: 4 heures
            24,   -- medium: 1 jour
            168,  -- low: 1 semaine
            720,  -- very_low: 1 mois
            2.0   -- Priorité de cache doublée
        );
    """
    )


def downgrade() -> None:
    """Suppression des tables de cache YFinance"""

    # Suppression des tables dans l'ordre inverse
    op.drop_table("precision_policies")
    op.drop_table("data_gaps")
    op.drop_table("cache_statistics")
    op.drop_table("timeline_metrics")
    op.drop_table("market_data_cache")
