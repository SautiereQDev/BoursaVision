"""
Modèles de Base de Données Optimisés pour le Cache des Données YFinance
=====================================================================

Modèles SQLAlchemy optimisés pour TimescaleDB avec gestion de la précision
temporelle et des stratégies de cache.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Enum,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from ..models.base import Base, DatabaseMixin
from ..models.mixins import TimestampMixin


class MarketDataCache(Base, DatabaseMixin, TimestampMixin):
    """
    Table principale pour le cache optimisé des données YFinance.

    Conçue pour TimescaleDB avec partitioning automatique par temps.
    Stocke les données OHLCV avec métadonnées de cache et précision.
    """

    __tablename__ = "market_data_cache"

    # Clé primaire composite pour TimescaleDB
    time = Column(TIMESTAMP(timezone=True), primary_key=True, nullable=False)
    symbol = Column(String(20), primary_key=True, nullable=False)
    interval_type = Column(String(5), primary_key=True, nullable=False)

    # Données OHLCV avec précision maximale
    open_price = Column(Numeric(20, 8), nullable=False)
    high_price = Column(Numeric(20, 8), nullable=False)
    low_price = Column(Numeric(20, 8), nullable=False)
    close_price = Column(Numeric(20, 8), nullable=False)
    adjusted_close = Column(Numeric(20, 8), nullable=True)
    volume = Column(BigInteger, nullable=True, default=0)

    # Métadonnées de cache et précision
    data_source = Column(String(20), nullable=False, default="yfinance")
    precision_level = Column(
        String(15), nullable=False, index=True  # Index pour les requêtes par précision
    )

    # Informations de cache
    cache_priority = Column(Integer, nullable=False, default=5)
    access_count = Column(Integer, nullable=False, default=0)
    last_accessed = Column(TIMESTAMP(timezone=True), nullable=True)
    cache_ttl_seconds = Column(Integer, nullable=False, default=3600)

    # Métadonnées d'origine YFinance
    yfinance_period = Column(String(10), nullable=True)  # 1d, 1mo, 1y, etc.
    yfinance_interval = Column(String(5), nullable=True)  # 1m, 5m, 1d, etc.

    # Données additionnelles pour l'analyse
    price_change_percent = Column(Numeric(8, 4), nullable=True)
    volume_sma_20 = Column(BigInteger, nullable=True)  # Volume moving average
    is_significant_movement = Column(Boolean, nullable=False, default=False)

    # Audit et traçabilité
    fetched_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    data_age_hours = Column(Numeric(10, 2), nullable=True)

    # Constraints
    __table_args__ = (
        # Index optimisés pour TimescaleDB
        Index("idx_market_data_cache_symbol_time", "symbol", "time"),
        Index("idx_market_data_cache_time_desc", "time", postgresql_using="btree"),
        Index("idx_market_data_cache_precision", "precision_level", "time"),
        Index("idx_market_data_cache_access", "last_accessed"),
        Index(
            "idx_market_data_cache_significant",
            "is_significant_movement",
            postgresql_where="is_significant_movement = true",
        ),
        # Constraint pour la cohérence des prix
        CheckConstraint(
            "high_price >= open_price AND high_price >= close_price",
            name="check_high_price_valid",
        ),
        CheckConstraint(
            "low_price <= open_price AND low_price <= close_price",
            name="check_low_price_valid",
        ),
        CheckConstraint("volume >= 0", name="check_volume_positive"),
        CheckConstraint(
            "precision_level IN ('ultra_high', 'high', 'medium', 'low', 'very_low')",
            name="check_precision_level",
        ),
        CheckConstraint(
            "data_source IN ('yfinance', 'yahoo_finance', 'alpha_vantage', 'internal_cache')",
            name="check_data_source",
        ),
        CheckConstraint(
            "cache_priority >= 1 AND cache_priority <= 10", name="check_cache_priority"
        ),
        # Extend existing pour éviter les erreurs de redéfinition
        {"extend_existing": True},
    )


class TimelineMetrics(Base, DatabaseMixin, TimestampMixin):
    """
    Métriques de qualité et performance des timelines par symbole.

    Stocke les statistiques agrégées pour optimiser les décisions de cache.
    """

    __tablename__ = "timeline_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)

    # Métriques de qualité des données
    total_points = Column(Integer, nullable=False, default=0)
    data_coverage_percent = Column(Numeric(5, 2), nullable=False, default=0)
    gaps_count = Column(Integer, nullable=False, default=0)
    significant_gaps_count = Column(Integer, nullable=False, default=0)

    # Distribution de précision (JSON)
    precision_distribution = Column(JSONB, nullable=True)

    # Plage temporelle des données
    oldest_point = Column(TIMESTAMP(timezone=True), nullable=True)
    newest_point = Column(TIMESTAMP(timezone=True), nullable=True)

    # Métriques de performance
    data_quality_score = Column(Numeric(5, 2), nullable=False, default=0)
    average_access_frequency = Column(Numeric(8, 2), nullable=False, default=0)
    cache_hit_rate = Column(Numeric(5, 2), nullable=False, default=0)

    # Dernière mise à jour
    last_calculated = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("idx_timeline_metrics_symbol", "symbol"),
        Index("idx_timeline_metrics_quality", "data_quality_score"),
        Index("idx_timeline_metrics_last_calc", "last_calculated"),
        UniqueConstraint("symbol", name="uq_timeline_metrics_symbol"),
        {"extend_existing": True},
    )


class CacheStatistics(Base, DatabaseMixin, TimestampMixin):
    """
    Statistiques globales du système de cache.

    Stocke les métriques de performance pour monitoring et optimisation.
    """

    __tablename__ = "cache_statistics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Période de mesure
    measurement_start = Column(TIMESTAMP(timezone=True), nullable=False)
    measurement_end = Column(TIMESTAMP(timezone=True), nullable=False)

    # Métriques de cache
    total_requests = Column(BigInteger, nullable=False, default=0)
    cache_hits = Column(BigInteger, nullable=False, default=0)
    cache_misses = Column(BigInteger, nullable=False, default=0)
    cache_hit_rate = Column(Numeric(5, 2), nullable=False, default=0)

    # Métriques YFinance
    yfinance_requests = Column(Integer, nullable=False, default=0)
    yfinance_errors = Column(Integer, nullable=False, default=0)
    average_response_time_ms = Column(Numeric(8, 2), nullable=True)

    # Métriques base de données
    db_reads = Column(Integer, nullable=False, default=0)
    db_writes = Column(Integer, nullable=False, default=0)
    db_deletes = Column(Integer, nullable=False, default=0)

    # Utilisation mémoire
    memory_usage_mb = Column(Numeric(10, 2), nullable=True)
    timelines_in_memory = Column(Integer, nullable=False, default=0)
    cache_entries_count = Column(Integer, nullable=False, default=0)

    # Évictions et nettoyage
    evictions_lru = Column(Integer, nullable=False, default=0)
    evictions_expired = Column(Integer, nullable=False, default=0)
    cleanup_operations = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("idx_cache_stats_period", "measurement_start", "measurement_end"),
        Index("idx_cache_stats_hit_rate", "cache_hit_rate"),
        {"extend_existing": True},
    )


class DataGaps(Base, DatabaseMixin, TimestampMixin):
    """
    Enregistrement des gaps détectés dans les timelines.

    Permet l'analyse et la correction proactive des données manquantes.
    """

    __tablename__ = "data_gaps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(20), nullable=False, index=True)

    # Définition du gap
    gap_start = Column(TIMESTAMP(timezone=True), nullable=False)
    gap_end = Column(TIMESTAMP(timezone=True), nullable=False)
    gap_duration_minutes = Column(Integer, nullable=False)

    # Contexte
    expected_interval = Column(String(5), nullable=False)
    interval_type = Column(String(5), nullable=False)

    # Classification
    is_significant = Column(Boolean, nullable=False, default=False)
    gap_reason = Column(String(100), nullable=True)

    # État
    is_resolved = Column(Boolean, nullable=False, default=False)
    resolution_method = Column(String(50), nullable=True)
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_data_gaps_symbol_time", "symbol", "gap_start"),
        Index("idx_data_gaps_significant", "is_significant"),
        Index(
            "idx_data_gaps_unresolved",
            "is_resolved",
            postgresql_where="is_resolved = false",
        ),
        {"extend_existing": True},
    )


class PrecisionPolicies(Base, DatabaseMixin, TimestampMixin):
    """
    Politiques de précision et de rétention par type de données.

    Configure les stratégies de cache selon les besoins métier.
    """

    __tablename__ = "precision_policies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Identification de la politique
    policy_name = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)

    # Critères d'application
    symbol_pattern = Column(String(50), nullable=True)  # Regex ou pattern
    interval_types = Column(JSONB, nullable=True)  # Liste des intervalles
    market_cap_min = Column(BigInteger, nullable=True)
    volume_min = Column(BigInteger, nullable=True)

    # Configuration de précision
    ultra_high_ttl_hours = Column(Integer, nullable=False, default=1)
    high_ttl_hours = Column(Integer, nullable=False, default=24)
    medium_ttl_hours = Column(Integer, nullable=False, default=168)  # 1 semaine
    low_ttl_hours = Column(Integer, nullable=False, default=720)  # 1 mois
    very_low_ttl_hours = Column(Integer, nullable=False, default=8760)  # 1 an

    # Stratégies de cache
    cache_priority_multiplier = Column(Numeric(3, 2), nullable=False, default=1.0)
    enable_predictive_caching = Column(Boolean, nullable=False, default=False)
    max_cache_points_per_symbol = Column(Integer, nullable=False, default=10000)

    # État
    is_active = Column(Boolean, nullable=False, default=True)
    priority = Column(
        Integer, nullable=False, default=100
    )  # Plus bas = plus prioritaire

    __table_args__ = (
        Index("idx_precision_policies_active", "is_active"),
        Index("idx_precision_policies_priority", "priority"),
        {"extend_existing": True},
    )


# Vue matérialisée pour les requêtes fréquentes
"""
-- Vue matérialisée pour les métriques en temps réel
CREATE MATERIALIZED VIEW market_data_cache_summary AS
SELECT 
    symbol,
    interval_type,
    precision_level,
    COUNT(*) as total_points,
    MIN(time) as oldest_data,
    MAX(time) as newest_data,
    AVG(access_count) as avg_access_count,
    SUM(CASE WHEN is_significant_movement THEN 1 ELSE 0 END) as significant_movements,
    AVG(volume) as avg_volume,
    EXTRACT(EPOCH FROM (MAX(time) - MIN(time))) / 3600 as timespan_hours
FROM market_data_cache
GROUP BY symbol, interval_type, precision_level;

-- Index sur la vue
CREATE UNIQUE INDEX idx_cache_summary_pk 
ON market_data_cache_summary (symbol, interval_type, precision_level);

-- Rafraîchissement automatique (à configurer avec un cron job)
-- REFRESH MATERIALIZED VIEW CONCURRENTLY market_data_cache_summary;
"""
