"""
Service de Cache Intelligent pour Données YFinance
=================================================

Service orchestrateur qui gère le cache intelligent des données YFinance
avec préservation de la précision temporelle et construction de timelines cohérentes.

Design Patterns:
- Facade Pattern: Interface simplifiée pour le cache complexe
- Strategy Pattern: Stratégies de cache selon les données
- Observer Pattern: Notifications de mise à jour
- Template Method: Template pour les opérations de cache
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

# Mock YFinance pour l'instant
try:
    import pandas as pd
    import yfinance as yf

    YF_AVAILABLE = True
except ImportError:
    yf = None
    pd = None
    YF_AVAILABLE = False

from ...domain.entities.market_data_timeline import (
    Currency,
    DataSource,
    IntervalType,
    MarketDataTimeline,
    Money,
    PrecisionLevel,
    TimelinePoint,
)
from ...domain.services.cache_strategies import (
    CacheConfig,
    MarketDataCacheManager,
    PrecisionStrategyFactory,
)

logger = logging.getLogger(__name__)


class YFinanceDataFetcher:
    """Fetcher optimisé pour YFinance avec gestion de la précision"""

    def __init__(self):
        self.request_count = 0
        self.last_request_time = None
        self.rate_limit_delay = 0.1  # 100ms entre requêtes

    async def fetch_historical_data(
        self, symbol: str, period: str = "1y", interval: str = "1d"
    ) -> List[TimelinePoint]:
        """Récupère les données historiques avec gestion du rate limiting"""
        if not YF_AVAILABLE:
            logger.warning("YFinance not available, returning mock data")
            return self._generate_mock_data(symbol, period, interval)

        # Rate limiting
        await self._apply_rate_limit()

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                logger.warning(f"No data returned for {symbol}")
                return []

            # Convertit en TimelinePoints
            points = []
            currency = self._get_currency_for_symbol(symbol)
            interval_type = self._yf_interval_to_enum(interval)

            for index, row in hist.iterrows():
                # Détermine le niveau de précision basé sur l'âge
                timestamp = index.to_pydatetime()
                if timestamp.tzinfo is None:
                    timestamp = timestamp.replace(tzinfo=timezone.utc)

                age_hours = (
                    datetime.now(timezone.utc) - timestamp
                ).total_seconds() / 3600
                precision_level = self._get_precision_for_age(age_hours)

                point = TimelinePoint(
                    timestamp=timestamp,
                    open_price=Money(
                        amount=Decimal(str(row["Open"])), currency=currency
                    ),
                    high_price=Money(
                        amount=Decimal(str(row["High"])), currency=currency
                    ),
                    low_price=Money(amount=Decimal(str(row["Low"])), currency=currency),
                    close_price=Money(
                        amount=Decimal(str(row["Close"])), currency=currency
                    ),
                    adjusted_close=Money(
                        amount=Decimal(str(row.get("Adj Close", row["Close"]))),
                        currency=currency,
                    ),
                    volume=int(row["Volume"])
                    if (pd and not pd.isna(row["Volume"]))
                    else 0,
                    interval_type=interval_type,
                    source=DataSource.YFINANCE,
                    precision_level=precision_level,
                )
                points.append(point)

            self.request_count += 1
            logger.info(
                f"Fetched {len(points)} points for {symbol} ({period}, {interval})"
            )
            return points

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return []

    async def _apply_rate_limit(self):
        """Applique le rate limiting"""
        if self.last_request_time:
            elapsed = datetime.now().timestamp() - self.last_request_time
            if elapsed < self.rate_limit_delay:
                await asyncio.sleep(self.rate_limit_delay - elapsed)

        self.last_request_time = datetime.now().timestamp()

    def _generate_mock_data(
        self, symbol: str, period: str, interval: str  # period utilisé dans la logique
    ) -> List[TimelinePoint]:
        """Génère des données mock pour les tests"""
        points = []
        currency = self._get_currency_for_symbol(symbol)
        interval_type = self._yf_interval_to_enum(interval)

        # Génère 30 jours de données mock
        start_date = datetime.now(timezone.utc) - timedelta(days=30)
        base_price = Decimal("100.0")

        for i in range(30):
            timestamp = start_date + timedelta(days=i)
            price_variation = Decimal(str((i % 10 - 5) * 0.01))  # Variation de ±5%

            open_price = base_price + price_variation
            high_price = open_price * Decimal("1.02")
            low_price = open_price * Decimal("0.98")
            close_price = open_price + (price_variation * Decimal("0.5"))

            age_hours = (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600
            precision_level = self._get_precision_for_age(age_hours)

            point = TimelinePoint(
                timestamp=timestamp,
                open_price=Money(amount=open_price, currency=currency),
                high_price=Money(amount=high_price, currency=currency),
                low_price=Money(amount=low_price, currency=currency),
                close_price=Money(amount=close_price, currency=currency),
                adjusted_close=Money(amount=close_price, currency=currency),
                volume=1000000 + (i * 10000),
                interval_type=interval_type,
                source=DataSource.YFINANCE,
                precision_level=precision_level,
            )
            points.append(point)

        return points

    def _get_currency_for_symbol(self, symbol: str) -> Currency:
        """Détermine la currency d'un symbole"""
        if any(suffix in symbol.upper() for suffix in [".TO", ".V"]):
            return Currency(code="CAD", name="Canadian Dollar", symbol="$")
        elif any(suffix in symbol.upper() for suffix in [".L", ".LON"]):
            return Currency(code="GBP", name="British Pound", symbol="£")
        elif any(suffix in symbol.upper() for suffix in [".PA", ".F"]):
            return Currency(code="EUR", name="Euro", symbol="€")
        else:
            return Currency(code="USD", name="US Dollar", symbol="$")

    def _yf_interval_to_enum(self, interval: str) -> IntervalType:
        """Convertit un interval YFinance en enum"""
        mapping = {
            "1m": IntervalType.ONE_MINUTE,
            "2m": IntervalType.TWO_MINUTES,
            "5m": IntervalType.FIVE_MINUTES,
            "15m": IntervalType.FIFTEEN_MINUTES,
            "30m": IntervalType.THIRTY_MINUTES,
            "60m": IntervalType.SIXTY_MINUTES,
            "90m": IntervalType.NINETY_MINUTES,
            "1d": IntervalType.ONE_DAY,
            "5d": IntervalType.FIVE_DAYS,
            "1wk": IntervalType.ONE_WEEK,
            "1mo": IntervalType.ONE_MONTH,
            "3mo": IntervalType.THREE_MONTHS,
        }
        return mapping.get(interval, IntervalType.ONE_DAY)

    def _get_precision_for_age(self, age_hours: float) -> PrecisionLevel:
        """Détermine le niveau de précision selon l'âge"""
        if age_hours < 24:
            return PrecisionLevel.ULTRA_HIGH
        elif age_hours < 168:  # 1 semaine
            return PrecisionLevel.HIGH
        elif age_hours < 720:  # 1 mois
            return PrecisionLevel.MEDIUM
        elif age_hours < 8760:  # 1 an
            return PrecisionLevel.LOW
        else:
            return PrecisionLevel.VERY_LOW


class MarketDataCacheService:
    """Service principal de cache intelligent pour les données de marché"""

    def __init__(
        self, cache_config: Optional[CacheConfig] = None, timeline_repository=None
    ):
        self.cache_config = cache_config or CacheConfig()
        self.cache_manager = MarketDataCacheManager(self.cache_config)
        self.timeline_repository = timeline_repository
        self.fetcher = YFinanceDataFetcher()
        self._timelines: Dict[str, MarketDataTimeline] = {}

        # Statistiques du service
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "db_reads": 0,
            "db_writes": 0,
            "yfinance_requests": 0,
            "timelines_loaded": 0,
        }

    async def get_timeline(
        self, symbol: str, force_refresh: bool = False
    ) -> Optional[MarketDataTimeline]:
        """Récupère la timeline complète d'un symbole"""
        symbol = symbol.upper()

        # Vérifie le cache mémoire
        if not force_refresh and symbol in self._timelines:
            logger.debug(f"Timeline found in memory cache for {symbol}")
            return self._timelines[symbol]

        # Charge depuis la base de données
        if self.timeline_repository:
            try:
                timeline = await self.timeline_repository.get_timeline(symbol)
                if timeline:
                    self._timelines[symbol] = timeline
                    self.stats["db_reads"] += 1
                    self.stats["timelines_loaded"] += 1
                    logger.info(f"Timeline loaded from database for {symbol}")
                    return timeline
            except Exception as e:
                logger.error(f"Error loading timeline from DB for {symbol}: {e}")

        # Crée une nouvelle timeline
        currency = self.fetcher._get_currency_for_symbol(symbol)
        timeline = MarketDataTimeline(symbol=symbol, currency=currency)
        self._timelines[symbol] = timeline
        self.stats["timelines_loaded"] += 1

        return timeline

    async def get_market_data(
        self,
        symbol: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        interval: IntervalType = IntervalType.ONE_DAY,
        max_age_hours: float = 1.0,
    ) -> List[TimelinePoint]:
        """
        Récupère les données de marché avec cache intelligent.

        Cette méthode implémente la logique de cache à plusieurs niveaux :
        1. Cache mémoire (timeline)
        2. Cache applicatif (cache manager)
        3. Base de données
        4. YFinance API
        """
        symbol = symbol.upper()

        # Paramètres par défaut
        if not end_time:
            end_time = datetime.now(timezone.utc)
        if not start_time:
            start_time = end_time - timedelta(days=365)  # 1 an par défaut

        # Récupère la timeline
        timeline = await self.get_timeline(symbol)
        if not timeline:
            logger.error(f"Could not create timeline for {symbol}")
            return []

        # Vérifie si on a besoin de rafraîchir
        needs_refresh = timeline.needs_refresh(interval, max_age_hours)

        if not needs_refresh:
            # Retourne les données du cache
            points = timeline.get_points_in_range(start_time, end_time, interval)
            self.stats["cache_hits"] += 1
            logger.debug(f"Returning {len(points)} cached points for {symbol}")
            return points

        # Fetch nouvelles données
        await self._refresh_timeline_data(timeline, interval, start_time, end_time)

        # Retourne les données mise à jour
        points = timeline.get_points_in_range(start_time, end_time, interval)
        logger.info(f"Returning {len(points)} refreshed points for {symbol}")
        return points

    async def _refresh_timeline_data(
        self,
        timeline: MarketDataTimeline,
        interval: IntervalType,
        start_time: datetime,
        end_time: datetime,
    ) -> None:
        """Rafraîchit les données d'une timeline"""
        symbol = timeline.symbol

        # Détermine la période YFinance appropriée
        yf_period, yf_interval = self._determine_yfinance_params(
            start_time, end_time, interval
        )

        # Fetch depuis YFinance
        try:
            new_points = await self.fetcher.fetch_historical_data(
                symbol, yf_period, yf_interval
            )

            if new_points:
                # Ajoute les nouveaux points à la timeline
                timeline.add_points(new_points)

                # Met en cache les points individuels
                for point in new_points:
                    self.cache_manager.put(symbol, point)

                # Sauvegarde en base si repository disponible
                if self.timeline_repository:
                    try:
                        await self.timeline_repository.save_timeline(timeline)
                        self.stats["db_writes"] += 1
                    except Exception as e:
                        logger.error(f"Error saving timeline to DB for {symbol}: {e}")

                self.stats["yfinance_requests"] += 1
                logger.info(f"Refreshed {len(new_points)} points for {symbol}")
            else:
                self.stats["cache_misses"] += 1

        except Exception as e:
            logger.error(f"Error refreshing data for {symbol}: {e}")
            self.stats["cache_misses"] += 1

    def _determine_yfinance_params(
        self, start_time: datetime, end_time: datetime, interval: IntervalType
    ) -> Tuple[str, str]:
        """Détermine les paramètres YFinance optimaux"""
        time_diff = end_time - start_time
        days = time_diff.days

        # Détermine la période
        if days <= 1:
            period = "1d"
        elif days <= 5:
            period = "5d"
        elif days <= 30:
            period = "1mo"
        elif days <= 90:
            period = "3mo"
        elif days <= 180:
            period = "6mo"
        elif days <= 365:
            period = "1y"
        elif days <= 730:
            period = "2y"
        elif days <= 1825:
            period = "5y"
        else:
            period = "max"

        # Mappe l'interval
        interval_mapping = {
            IntervalType.ONE_MINUTE: "1m",
            IntervalType.TWO_MINUTES: "2m",
            IntervalType.FIVE_MINUTES: "5m",
            IntervalType.FIFTEEN_MINUTES: "15m",
            IntervalType.THIRTY_MINUTES: "30m",
            IntervalType.SIXTY_MINUTES: "60m",
            IntervalType.NINETY_MINUTES: "90m",
            IntervalType.ONE_DAY: "1d",
            IntervalType.FIVE_DAYS: "5d",
            IntervalType.ONE_WEEK: "1wk",
            IntervalType.ONE_MONTH: "1mo",
            IntervalType.THREE_MONTHS: "3mo",
        }

        yf_interval = interval_mapping.get(interval, "1d")

        return period, yf_interval

    async def get_latest_price(self, symbol: str) -> Optional[Money]:
        """Récupère le dernier prix d'un symbole"""
        timeline = await self.get_timeline(symbol)
        if timeline:
            return timeline.get_latest_price()
        return None

    async def bulk_refresh_symbols(
        self,
        symbols: List[str],
        interval: IntervalType = IntervalType.ONE_DAY,
        max_concurrent: int = 10,
    ) -> Dict[str, bool]:
        """Rafraîchit plusieurs symboles en parallèle"""
        results = {}

        # Traite par batch pour éviter le rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)

        async def refresh_symbol(symbol: str) -> bool:
            async with semaphore:
                try:
                    timeline = await self.get_timeline(symbol)
                    if timeline and timeline.needs_refresh(interval):
                        await self._refresh_timeline_data(
                            timeline,
                            interval,
                            datetime.now(timezone.utc) - timedelta(days=30),
                            datetime.now(timezone.utc),
                        )
                        return True
                    return False
                except Exception as e:
                    logger.error(f"Error refreshing {symbol}: {e}")
                    return False

        # Lance les tâches en parallèle
        tasks = [refresh_symbol(symbol) for symbol in symbols]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Compile les résultats
        for symbol, result in zip(symbols, task_results):
            if isinstance(result, Exception):
                results[symbol] = False
                logger.error(f"Error refreshing {symbol}: {result}")
            else:
                results[symbol] = bool(result)

        return results

    def get_cache_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes du cache"""
        cache_stats = self.cache_manager.get_stats()

        return {
            "service_stats": self.stats,
            "cache_manager_stats": cache_stats,
            "timelines_in_memory": len(self._timelines),
            "total_requests": self.stats["cache_hits"] + self.stats["cache_misses"],
            "cache_hit_rate": (
                self.stats["cache_hits"]
                / max(1, self.stats["cache_hits"] + self.stats["cache_misses"])
            )
            * 100,
        }

    def clear_cache(self, symbol: Optional[str] = None) -> None:
        """Vide le cache"""
        if symbol:
            symbol = symbol.upper()
            if symbol in self._timelines:
                del self._timelines[symbol]
            self.cache_manager.clear_symbol(symbol)
        else:
            self._timelines.clear()
            self.cache_manager.clear_all()

    def get_loaded_symbols(self) -> List[str]:
        """Retourne la liste des symboles actuellement chargés en mémoire"""
        return list(self._timelines.keys())

    async def cleanup_old_data(
        self,
        older_than_days: int = 30,
        precision_levels: Optional[List[PrecisionLevel]] = None,
    ) -> Dict[str, int]:
        """Nettoie les anciennes données selon les critères"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=older_than_days)
        results: Dict[str, int] = {}

        if not self.timeline_repository:
            logger.warning("No repository available for cleanup")
            return results

        if precision_levels is None:
            precision_levels = [PrecisionLevel.LOW, PrecisionLevel.VERY_LOW]

        # Nettoie pour chaque symbole en mémoire
        for symbol, timeline in self._timelines.items():
            try:
                for precision_level in precision_levels:
                    count = await self.timeline_repository.delete_old_points(
                        symbol, cutoff_date, precision_level
                    )
                    results[f"{symbol}_{precision_level.value}"] = count
            except Exception as e:
                logger.error(f"Error cleaning up {symbol}: {e}")
                results[symbol] = 0

        return results
