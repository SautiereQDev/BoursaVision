"""
Stratégies de Précision et de Cache pour Données YFinance
========================================================

Ce module implémente les stratégies de cache intelligentes pour optimiser
la récupération et le stockage des données YFinance en fonction de leur âge
et de leur fréquence d'accès.

Design Patterns:
- Strategy Pattern: Différentes stratégies de cache selon le type de données
- Factory Pattern: Factory pour créer les bonnes stratégies
- Observer Pattern: Notifications de mise à jour du cache
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol

from ..entities.market_data_timeline import (
    DataSource,
    IntervalType,
    PrecisionLevel,
    TimelinePoint,
)

logger = logging.getLogger(__name__)


class CacheStrategy(Protocol):
    """Interface pour les stratégies de cache"""

    def should_cache(self, point: TimelinePoint) -> bool:
        """Détermine si un point doit être mis en cache"""
        ...

    def get_cache_ttl(self, point: TimelinePoint) -> int:
        """Retourne la durée de vie en cache en secondes"""
        ...

    def get_priority(self, point: TimelinePoint) -> int:
        """Retourne la priorité de cache (1-10)"""
        ...


@dataclass
class CacheConfig:
    """Configuration du cache pour les données de marché"""

    # TTLs par niveau de précision (en secondes)
    ultra_high_ttl: int = 300  # 5 minutes
    high_ttl: int = 3600  # 1 heure
    medium_ttl: int = 21600  # 6 heures
    low_ttl: int = 86400  # 24 heures
    very_low_ttl: int = 604800  # 7 jours

    # Tailles de cache par intervalle
    max_points_per_symbol: Optional[Dict[IntervalType, int]] = None

    # Politiques de purge
    enable_lru_eviction: bool = True
    enable_precision_based_eviction: bool = True
    max_memory_mb: int = 1024

    def __post_init__(self):
        if self.max_points_per_symbol is None:
            self.max_points_per_symbol = {
                IntervalType.ONE_MINUTE: 1440,  # 1 jour
                IntervalType.FIVE_MINUTES: 2016,  # 1 semaine
                IntervalType.FIFTEEN_MINUTES: 2688,  # 4 semaines
                IntervalType.SIXTY_MINUTES: 2160,  # 3 mois
                IntervalType.ONE_DAY: 1000,  # ~3 ans
                IntervalType.ONE_WEEK: 520,  # 10 ans
                IntervalType.ONE_MONTH: 240,  # 20 ans
            }


class UltraHighPrecisionStrategy:
    """Stratégie pour données ultra haute précision (< 1 jour)"""

    def __init__(self, config: CacheConfig):
        self.config = config

    def should_cache(self, point: TimelinePoint) -> bool:
        """Cache toujours les données ultra précises"""
        return True

    def get_cache_ttl(self, point: TimelinePoint) -> int:
        """TTL court pour données fraîches"""
        return self.config.ultra_high_ttl

    def get_priority(self, point: TimelinePoint) -> int:
        """Priorité maximale pour données récentes"""
        return 10


class HighPrecisionStrategy:
    """Stratégie pour données haute précision (1 jour - 1 semaine)"""

    def __init__(self, config: CacheConfig):
        self.config = config

    def should_cache(self, point: TimelinePoint) -> bool:
        """Cache selon l'importance du symbole et l'activité"""
        # Logique simplifiée - cache tout pour l'instant
        return True

    def get_cache_ttl(self, point: TimelinePoint) -> int:
        """TTL modéré"""
        return self.config.high_ttl

    def get_priority(self, point: TimelinePoint) -> int:
        """Priorité élevée"""
        return 8


class MediumPrecisionStrategy:
    """Stratégie pour données précision moyenne (1 semaine - 1 mois)"""

    def __init__(self, config: CacheConfig):
        self.config = config

    def should_cache(self, point: TimelinePoint) -> bool:
        """Cache sélectivement"""
        # Priorise les gros volumes et les mouvements significatifs
        return point.volume > 100000 or abs(point.price_change_percent) > 2.0

    def get_cache_ttl(self, point: TimelinePoint) -> int:
        """TTL plus long"""
        return self.config.medium_ttl

    def get_priority(self, point: TimelinePoint) -> int:
        """Priorité moyenne"""
        return 5


class LowPrecisionStrategy:
    """Stratégie pour données basse précision (1 mois - 1 an)"""

    def __init__(self, config: CacheConfig):
        self.config = config

    def should_cache(self, point: TimelinePoint) -> bool:
        """Cache uniquement les données importantes"""
        # Cache les points avec mouvements significatifs ou volumes élevés
        return point.volume > 500000 or abs(point.price_change_percent) > 5.0

    def get_cache_ttl(self, point: TimelinePoint) -> int:
        """TTL long"""
        return self.config.low_ttl

    def get_priority(self, point: TimelinePoint) -> int:
        """Priorité basse"""
        return 3


class VeryLowPrecisionStrategy:
    """Stratégie pour données très basse précision (> 1 an)"""

    def __init__(self, config: CacheConfig):
        self.config = config

    def should_cache(self, point: TimelinePoint) -> bool:
        """Cache très sélectivement"""
        # Uniquement les événements majeurs
        return abs(point.price_change_percent) > 10.0

    def get_cache_ttl(self, point: TimelinePoint) -> int:
        """TTL très long"""
        return self.config.very_low_ttl

    def get_priority(self, point: TimelinePoint) -> int:
        """Priorité minimale"""
        return 1


class PrecisionStrategyFactory:
    """Factory pour créer les stratégies de précision"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self._strategies: Dict[PrecisionLevel, CacheStrategy] = {
            PrecisionLevel.ULTRA_HIGH: UltraHighPrecisionStrategy(config),
            PrecisionLevel.HIGH: HighPrecisionStrategy(config),
            PrecisionLevel.MEDIUM: MediumPrecisionStrategy(config),
            PrecisionLevel.LOW: LowPrecisionStrategy(config),
            PrecisionLevel.VERY_LOW: VeryLowPrecisionStrategy(config),
        }

    def get_strategy(self, precision_level: PrecisionLevel) -> CacheStrategy:
        """Retourne la stratégie appropriée"""
        return self._strategies[precision_level]

    def get_strategy_for_age(self, age_hours: float) -> CacheStrategy:
        """Retourne la stratégie basée sur l'âge des données"""
        if age_hours < 24:
            level = PrecisionLevel.ULTRA_HIGH
        elif age_hours < 168:  # 1 semaine
            level = PrecisionLevel.HIGH
        elif age_hours < 720:  # 1 mois
            level = PrecisionLevel.MEDIUM
        elif age_hours < 8760:  # 1 an
            level = PrecisionLevel.LOW
        else:
            level = PrecisionLevel.VERY_LOW

        return self.get_strategy(level)


@dataclass
class CacheEntry:
    """Entrée de cache avec métadonnées"""

    point: TimelinePoint
    cached_at: datetime
    access_count: int
    last_accessed: datetime
    priority: int
    ttl_seconds: int

    @property
    def is_expired(self) -> bool:
        """Vérifie si l'entrée a expiré"""
        age = (datetime.now(timezone.utc) - self.cached_at).total_seconds()
        return age > self.ttl_seconds

    @property
    def age_seconds(self) -> float:
        """Âge de l'entrée en secondes"""
        return (datetime.now(timezone.utc) - self.cached_at).total_seconds()

    def access(self) -> None:
        """Marque l'entrée comme accédée"""
        self.access_count += 1
        self.last_accessed = datetime.now(timezone.utc)


class MarketDataCacheManager:
    """Gestionnaire de cache intelligent pour les données de marché"""

    def __init__(self, config: CacheConfig):
        self.config = config
        self.strategy_factory = PrecisionStrategyFactory(config)
        self._cache: Dict[str, Dict[datetime, CacheEntry]] = {}
        self._access_log: List[str] = []
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "total_size": 0}

    def _generate_key(
        self, symbol: str, timestamp: datetime, interval: IntervalType
    ) -> str:
        """Génère une clé de cache"""
        return f"{symbol}:{interval.value}:{timestamp.isoformat()}"

    def get(
        self, symbol: str, timestamp: datetime, interval: IntervalType
    ) -> Optional[TimelinePoint]:
        """Récupère un point du cache"""
        if symbol not in self._cache:
            self._stats["misses"] += 1
            return None

        symbol_cache = self._cache[symbol]
        if timestamp not in symbol_cache:
            self._stats["misses"] += 1
            return None

        entry = symbol_cache[timestamp]

        # Vérifie l'expiration
        if entry.is_expired:
            del symbol_cache[timestamp]
            self._stats["misses"] += 1
            return None

        # Met à jour les statistiques d'accès
        entry.access()
        self._stats["hits"] += 1

        # Log pour LRU
        cache_key = self._generate_key(symbol, timestamp, interval)
        if cache_key in self._access_log:
            self._access_log.remove(cache_key)
        self._access_log.append(cache_key)

        return entry.point

    def put(self, symbol: str, point: TimelinePoint) -> bool:
        """Stocke un point dans le cache"""
        # Détermine la stratégie à utiliser
        age_hours = point.get_age_in_hours()
        strategy = self.strategy_factory.get_strategy_for_age(age_hours)

        # Vérifie si on doit mettre en cache
        if not strategy.should_cache(point):
            return False

        # Crée l'entrée de cache
        entry = CacheEntry(
            point=point,
            cached_at=datetime.now(timezone.utc),
            access_count=0,
            last_accessed=datetime.now(timezone.utc),
            priority=strategy.get_priority(point),
            ttl_seconds=strategy.get_cache_ttl(point),
        )

        # Initialise le cache du symbole si nécessaire
        if symbol not in self._cache:
            self._cache[symbol] = {}

        # Stocke l'entrée
        self._cache[symbol][point.timestamp] = entry
        self._stats["total_size"] += 1

        # Log pour LRU
        cache_key = self._generate_key(symbol, point.timestamp, point.interval_type)
        self._access_log.append(cache_key)

        # Déclenche l'éviction si nécessaire
        self._maybe_evict()

        return True

    def _maybe_evict(self) -> None:
        """Déclenche l'éviction si nécessaire"""
        # Éviction basée sur la taille
        if self.config.max_points_per_symbol:
            max_entries = sum(self.config.max_points_per_symbol.values())

            if self._stats["total_size"] > max_entries:
                self._evict_lru()

        # Éviction basée sur l'expiration
        self._evict_expired()

    def _evict_lru(self) -> None:
        """Éviction LRU"""
        if not self._access_log:
            return

        # Retire le plus ancien accès
        oldest_key = self._access_log.pop(0)
        parts = oldest_key.split(":")
        if len(parts) >= 3:
            symbol = parts[0]
            timestamp_str = ":".join(parts[2:])
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                if symbol in self._cache and timestamp in self._cache[symbol]:
                    del self._cache[symbol][timestamp]
                    self._stats["total_size"] -= 1
                    self._stats["evictions"] += 1
            except ValueError:
                pass

    def _evict_expired(self) -> None:
        """Éviction des entrées expirées"""
        for symbol in self._cache:
            symbol_cache = self._cache[symbol]
            expired_timestamps = [
                ts for ts, entry in symbol_cache.items() if entry.is_expired
            ]

            for ts in expired_timestamps:
                del symbol_cache[ts]
                self._stats["total_size"] -= 1
                self._stats["evictions"] += 1

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du cache"""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / max(1, total_requests) * 100

        return {
            **self._stats,
            "hit_rate": hit_rate,
            "total_requests": total_requests,
            "symbols_cached": len(self._cache),
        }

    def clear_symbol(self, symbol: str) -> None:
        """Vide le cache pour un symbole"""
        if symbol in self._cache:
            count = len(self._cache[symbol])
            del self._cache[symbol]
            self._stats["total_size"] -= count

    def clear_all(self) -> None:
        """Vide tout le cache"""
        self._cache.clear()
        self._access_log.clear()
        self._stats["total_size"] = 0

    def get_cached_symbols(self) -> List[str]:
        """Retourne la liste des symboles en cache"""
        return list(self._cache.keys())

    def get_symbol_cache_info(self, symbol: str) -> Dict[str, Any]:
        """Retourne des infos sur le cache d'un symbole"""
        if symbol not in self._cache:
            return {"exists": False}

        symbol_cache = self._cache[symbol]
        now = datetime.now(timezone.utc)

        # Analyse des entrées
        total_entries = len(symbol_cache)
        expired_count = sum(1 for entry in symbol_cache.values() if entry.is_expired)
        avg_age = sum(
            (now - entry.cached_at).total_seconds() for entry in symbol_cache.values()
        ) / max(1, total_entries)

        precision_dist: Dict[str, int] = {}
        for entry in symbol_cache.values():
            level = entry.point.precision_level
            precision_dist[level.value] = precision_dist.get(level.value, 0) + 1

        return {
            "exists": True,
            "total_entries": total_entries,
            "expired_entries": expired_count,
            "average_age_seconds": avg_age,
            "precision_distribution": precision_dist,
            "oldest_entry": min(
                (entry.cached_at for entry in symbol_cache.values()), default=None
            ),
            "newest_entry": max(
                (entry.cached_at for entry in symbol_cache.values()), default=None
            ),
        }
