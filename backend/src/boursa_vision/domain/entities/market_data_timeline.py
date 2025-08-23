"""
Market Data Timeline Entity - Gestion des Données Temporelles YFinance
====================================================================

Entité métier pour gérer les timelines de données de marché avec préservation
de la précision temporelle des données YFinance.

Design Patterns:
- Value Object: TimelinePoint pour encapsuler les données de prix
- Entity: MarketDataTimeline pour la logique métier
- Strategy: DataPrecisionStrategy pour gérer la précision selon le temps
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


# Temporary Money and Currency classes until we can import them properly
@dataclass(frozen=True)
class Currency:
    """Temporary Currency value object"""

    code: str
    name: str
    symbol: str = ""


@dataclass(frozen=True)
class Money:
    """Temporary Money value object"""

    amount: Decimal
    currency: Currency

    def __post_init__(self):
        if not isinstance(self.amount, Decimal):
            object.__setattr__(self, "amount", Decimal(str(self.amount)))


class AggregateRoot:
    """Temporary base class"""

    def __init__(self):
        self.id = uuid4()


class IntervalType(str, Enum):
    """Types d'intervalles supportés par YFinance"""

    # Intraday (haute fréquence)
    ONE_MINUTE = "1m"
    TWO_MINUTES = "2m"
    FIVE_MINUTES = "5m"
    FIFTEEN_MINUTES = "15m"
    THIRTY_MINUTES = "30m"
    SIXTY_MINUTES = "60m"
    NINETY_MINUTES = "90m"

    # Daily et plus
    ONE_DAY = "1d"
    FIVE_DAYS = "5d"
    ONE_WEEK = "1wk"
    ONE_MONTH = "1mo"
    THREE_MONTHS = "3mo"


class DataSource(str, Enum):
    """Sources de données de marché"""

    YFINANCE = "yfinance"
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    QUANDL = "quandl"
    INTERNAL_CACHE = "internal_cache"


class PrecisionLevel(str, Enum):
    """Niveaux de précision des données"""

    ULTRA_HIGH = "ultra_high"  # < 1 jour
    HIGH = "high"  # 1 jour - 1 semaine
    MEDIUM = "medium"  # 1 semaine - 1 mois
    LOW = "low"  # 1 mois - 1 an
    VERY_LOW = "very_low"  # > 1 an


@dataclass(frozen=True)
class TimelinePoint:
    """Point temporel dans une timeline de données de marché"""

    timestamp: datetime
    open_price: Money
    high_price: Money
    low_price: Money
    close_price: Money
    adjusted_close: Money
    volume: int
    interval_type: IntervalType
    source: DataSource
    precision_level: PrecisionLevel
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self):
        """Validation des données après initialisation"""
        if self.high_price.amount < max(
            self.open_price.amount, self.close_price.amount
        ):
            raise ValueError("High price cannot be lower than open/close price")

        if self.low_price.amount > min(self.open_price.amount, self.close_price.amount):
            raise ValueError("Low price cannot be higher than open/close price")

        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

    @property
    def price_change(self) -> Money:
        """Variation de prix sur la période"""
        return Money(
            amount=self.close_price.amount - self.open_price.amount,
            currency=self.close_price.currency,
        )

    @property
    def price_change_percent(self) -> float:
        """Variation de prix en pourcentage"""
        if self.open_price.amount == 0:
            return 0.0
        return float(
            (
                (self.close_price.amount - self.open_price.amount)
                / self.open_price.amount
            )
            * 100
        )

    @property
    def typical_price(self) -> Money:
        """Prix typique (HLC/3)"""
        typical = (
            self.high_price.amount + self.low_price.amount + self.close_price.amount
        ) / 3
        return Money(amount=typical, currency=self.close_price.currency)

    def is_bullish(self) -> bool:
        """Détermine si le point est haussier"""
        return self.close_price.amount > self.open_price.amount

    def get_age_in_hours(self) -> float:
        """Retourne l'âge du point en heures"""
        now = datetime.now(UTC)
        return (now - self.timestamp).total_seconds() / 3600


@dataclass
class DataGap:
    """Représente un gap dans les données de timeline"""

    start_time: datetime
    end_time: datetime
    expected_interval: IntervalType
    gap_duration: timedelta
    reason: str = "unknown"

    @property
    def duration_minutes(self) -> float:
        """Durée du gap en minutes"""
        return self.gap_duration.total_seconds() / 60

    def is_significant(self) -> bool:
        """Détermine si le gap est significatif"""
        # Un gap est significatif s'il dépasse 3 fois l'intervalle attendu
        expected_minutes = self._interval_to_minutes(self.expected_interval)
        return self.duration_minutes > (expected_minutes * 3)

    def _interval_to_minutes(self, interval: IntervalType) -> int:
        """Convertit un interval en minutes"""
        mapping = {
            IntervalType.ONE_MINUTE: 1,
            IntervalType.TWO_MINUTES: 2,
            IntervalType.FIVE_MINUTES: 5,
            IntervalType.FIFTEEN_MINUTES: 15,
            IntervalType.THIRTY_MINUTES: 30,
            IntervalType.SIXTY_MINUTES: 60,
            IntervalType.NINETY_MINUTES: 90,
            IntervalType.ONE_DAY: 1440,
            IntervalType.ONE_WEEK: 10080,
        }
        return mapping.get(interval, 1440)


@dataclass
class TimelineMetrics:
    """Métriques sur la qualité d'une timeline"""

    total_points: int
    data_coverage_percent: float
    gaps_count: int
    significant_gaps_count: int
    precision_distribution: dict[PrecisionLevel, int]
    oldest_point: datetime | None
    newest_point: datetime | None

    @property
    def data_quality_score(self) -> float:
        """Score de qualité des données (0-100)"""
        if self.total_points == 0:
            return 0.0

        # Facteurs de qualité
        coverage_score = self.data_coverage_percent
        gaps_penalty = min(50, self.significant_gaps_count * 10)
        precision_bonus = self._calculate_precision_bonus()

        return max(0, min(100, coverage_score - gaps_penalty + precision_bonus))

    def _calculate_precision_bonus(self) -> float:
        """Calcule le bonus basé sur la distribution de précision"""
        if not self.precision_distribution:
            return 0.0

        weights = {
            PrecisionLevel.ULTRA_HIGH: 5,
            PrecisionLevel.HIGH: 3,
            PrecisionLevel.MEDIUM: 1,
            PrecisionLevel.LOW: 0,
            PrecisionLevel.VERY_LOW: -1,
        }

        total_weighted = sum(
            count * weights.get(level, 0)
            for level, count in self.precision_distribution.items()
        )

        return min(20, total_weighted / self.total_points)


class MarketDataTimeline(AggregateRoot):
    """
    Timeline de données de marché pour un symbole financier.

    Gère la cohérence temporelle et la précision des données YFinance
    en fonction de leur âge et de leur fréquence.
    """

    def __init__(
        self, symbol: str, currency: Currency, timeline_id: UUID | None = None
    ):
        super().__init__()
        self.id = timeline_id or uuid4()
        self.symbol = symbol.upper()
        self.currency = currency
        self._points: dict[datetime, TimelinePoint] = {}
        self._gaps: list[DataGap] = []
        self._is_dirty = False
        self.created_at = datetime.now(UTC)
        self.updated_at = self.created_at

    @property
    def points(self) -> list[TimelinePoint]:
        """Retourne tous les points triés par timestamp"""
        return sorted(self._points.values(), key=lambda p: p.timestamp)

    @property
    def latest_point(self) -> TimelinePoint | None:
        """Retourne le point le plus récent"""
        if not self._points:
            return None
        return max(self._points.values(), key=lambda p: p.timestamp)

    @property
    def oldest_point(self) -> TimelinePoint | None:
        """Retourne le point le plus ancien"""
        if not self._points:
            return None
        return min(self._points.values(), key=lambda p: p.timestamp)

    def add_point(self, point: TimelinePoint) -> None:
        """Ajoute un point à la timeline avec validation"""
        if point.open_price.currency != self.currency:
            raise ValueError(
                f"Currency mismatch: expected {self.currency}, got {point.open_price.currency}"
            )

        # Vérification de doublons et mise à jour intelligente
        if point.timestamp in self._points:
            existing = self._points[point.timestamp]
            should_update = (
                existing.source == DataSource.INTERNAL_CACHE
                and point.source != DataSource.INTERNAL_CACHE
            ) or (point.precision_level.value < existing.precision_level.value)
            if should_update:
                self._points[point.timestamp] = point
                self._is_dirty = True
        else:
            self._points[point.timestamp] = point
            self._is_dirty = True

        self.updated_at = datetime.now(UTC)
        self._update_gaps()

    def add_points(self, points: list[TimelinePoint]) -> None:
        """Ajoute plusieurs points en lot"""
        for point in points:
            # Ne pas mettre à jour les gaps à chaque point pour performance
            if point.open_price.currency != self.currency:
                continue

            if point.timestamp in self._points:
                existing = self._points[point.timestamp]
                if (
                    existing.source == DataSource.INTERNAL_CACHE
                    and point.source != DataSource.INTERNAL_CACHE
                ) or (point.precision_level.value < existing.precision_level.value):
                    self._points[point.timestamp] = point
                    self._is_dirty = True
            else:
                self._points[point.timestamp] = point
                self._is_dirty = True

        self.updated_at = datetime.now(UTC)
        self._update_gaps()

    def get_points_in_range(
        self,
        start_time: datetime,
        end_time: datetime,
        interval_type: IntervalType | None = None,
    ) -> list[TimelinePoint]:
        """Récupère les points dans une plage temporelle"""
        points = [
            point
            for point in self._points.values()
            if start_time <= point.timestamp <= end_time
        ]

        if interval_type:
            points = [p for p in points if p.interval_type == interval_type]

        return sorted(points, key=lambda p: p.timestamp)

    def get_latest_price(self) -> Money | None:
        """Retourne le dernier prix de clôture"""
        latest = self.latest_point
        return latest.close_price if latest else None

    def needs_refresh(
        self, interval_type: IntervalType, max_age_hours: float = 1.0
    ) -> bool:
        """Détermine si la timeline a besoin d'être rafraîchie"""
        if not self._points:
            return True

        # Trouve le point le plus récent pour cet intervalle
        interval_points = [
            p for p in self._points.values() if p.interval_type == interval_type
        ]
        if not interval_points:
            return True

        latest = max(interval_points, key=lambda p: p.timestamp)
        age_hours = latest.get_age_in_hours()

        return age_hours > max_age_hours

    def get_precision_for_age(self, age_hours: float) -> PrecisionLevel:
        """Détermine le niveau de précision requis selon l'âge des données"""
        if age_hours < 24:  # < 1 jour
            return PrecisionLevel.ULTRA_HIGH
        elif age_hours < 168:  # < 1 semaine
            return PrecisionLevel.HIGH
        elif age_hours < 720:  # < 1 mois
            return PrecisionLevel.MEDIUM
        elif age_hours < 8760:  # < 1 an
            return PrecisionLevel.LOW
        else:
            return PrecisionLevel.VERY_LOW

    def get_gaps(self) -> list[DataGap]:
        """Retourne la liste des gaps détectés"""
        return self._gaps.copy()

    def get_metrics(self) -> TimelineMetrics:
        """Calcule les métriques de qualité de la timeline"""
        if not self._points:
            return TimelineMetrics(
                total_points=0,
                data_coverage_percent=0.0,
                gaps_count=0,
                significant_gaps_count=0,
                precision_distribution={},
                oldest_point=None,
                newest_point=None,
            )

        # Distribution de précision
        precision_dist: dict[PrecisionLevel, int] = {}
        for point in self._points.values():
            level = point.precision_level
            precision_dist[level] = precision_dist.get(level, 0) + 1

        # Calcul de couverture (simplifié)
        if self.latest_point and self.oldest_point:
            total_timespan = (
                self.latest_point.timestamp - self.oldest_point.timestamp
            ).total_seconds()
            expected_points = total_timespan / 3600  # estimation 1 point par heure
            coverage = min(100, (len(self._points) / max(1, expected_points)) * 100)
        else:
            coverage = 0.0

        significant_gaps = len([g for g in self._gaps if g.is_significant()])

        return TimelineMetrics(
            total_points=len(self._points),
            data_coverage_percent=coverage,
            gaps_count=len(self._gaps),
            significant_gaps_count=significant_gaps,
            precision_distribution=precision_dist,
            oldest_point=self.oldest_point.timestamp if self.oldest_point else None,
            newest_point=self.latest_point.timestamp if self.latest_point else None,
        )

    def _update_gaps(self) -> None:
        """Met à jour la détection des gaps dans les données"""
        if len(self._points) < 2:
            self._gaps = []
            return

        sorted_points = self.points
        gaps = []

        for i in range(len(sorted_points) - 1):
            current = sorted_points[i]
            next_point = sorted_points[i + 1]

            time_diff = next_point.timestamp - current.timestamp
            expected_interval = self._determine_expected_interval(current)

            if self._is_gap_significant(time_diff, expected_interval):
                gap = DataGap(
                    start_time=current.timestamp,
                    end_time=next_point.timestamp,
                    expected_interval=expected_interval,
                    gap_duration=time_diff,
                    reason="Missing data points",
                )
                gaps.append(gap)

        self._gaps = gaps

    def _determine_expected_interval(self, current: TimelinePoint) -> IntervalType:
        """Détermine l'intervalle attendu entre deux points"""
        # Logique simplifiée - utilise l'intervalle du point actuel
        return current.interval_type

    def _is_gap_significant(
        self, actual_gap: timedelta, expected_interval: IntervalType
    ) -> bool:
        """Détermine si un gap est significatif"""
        expected_minutes = self._interval_to_minutes(expected_interval)
        actual_minutes = actual_gap.total_seconds() / 60
        return actual_minutes > (expected_minutes * 2)  # Seuil : 2x l'intervalle

    def _interval_to_minutes(self, interval: IntervalType) -> int:
        """Convertit un interval en minutes"""
        mapping = {
            IntervalType.ONE_MINUTE: 1,
            IntervalType.TWO_MINUTES: 2,
            IntervalType.FIVE_MINUTES: 5,
            IntervalType.FIFTEEN_MINUTES: 15,
            IntervalType.THIRTY_MINUTES: 30,
            IntervalType.SIXTY_MINUTES: 60,
            IntervalType.NINETY_MINUTES: 90,
            IntervalType.ONE_DAY: 1440,
            IntervalType.ONE_WEEK: 10080,
        }
        return mapping.get(interval, 1440)
