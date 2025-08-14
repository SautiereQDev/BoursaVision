"""
Repository pour les Timelines de Données de Marché
=================================================

Repository pattern pour la persistance des timelines de données YFinance
avec optimisations TimescaleDB.

Design Patterns:
- Repository Pattern: Abstraction de la persistance
- Unit of Work: Gestion transactionnelle des timelines
- Specification Pattern: Requêtes complexes typées
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol


# Mock SQLAlchemy imports for now
class AsyncSession:
    """Mock AsyncSession"""

    async def execute(self, query):
        pass

    async def merge(self, obj):
        pass

    async def flush(self):
        pass

    async def rollback(self):
        pass


class IntegrityError(Exception):
    """Mock IntegrityError"""

    pass


def and_(*args):
    pass


def desc(col):
    pass


def func():
    pass


def select(model):
    pass


from ...infrastructure.persistence.models.market_data import MarketData
from ..entities.market_data_timeline import (
    DataSource,
    IntervalType,
    MarketDataTimeline,
    PrecisionLevel,
    TimelinePoint,
)


class IMarketDataTimelineRepository(Protocol):
    """Interface du repository pour les timelines"""

    async def get_timeline(self, symbol: str) -> Optional[MarketDataTimeline]:
        """Récupère la timeline complète d'un symbole"""
        ...

    async def save_timeline(self, timeline: MarketDataTimeline) -> MarketDataTimeline:
        """Sauvegarde une timeline"""
        ...

    async def get_points_in_range(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        interval_type: Optional[IntervalType] = None,
    ) -> List[TimelinePoint]:
        """Récupère les points dans une plage temporelle"""
        ...

    async def get_latest_point(
        self, symbol: str, interval_type: IntervalType
    ) -> Optional[TimelinePoint]:
        """Récupère le point le plus récent pour un symbole et intervalle"""
        ...

    async def bulk_save_points(self, symbol: str, points: List[TimelinePoint]) -> int:
        """Sauvegarde en lot des points de timeline"""
        ...

    async def delete_old_points(
        self,
        symbol: str,
        older_than: datetime,
        precision_level: Optional[PrecisionLevel] = None,
    ) -> int:
        """Supprime les anciens points selon les critères"""
        ...


class SqlAlchemyMarketDataTimelineRepository:
    """Repository SQLAlchemy optimisé pour TimescaleDB"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_timeline(self, symbol: str) -> Optional[MarketDataTimeline]:
        """Récupère la timeline complète d'un symbole"""
        # Requête optimisée avec index sur symbol + time
        query = (
            select(MarketData)
            .where(MarketData.symbol == symbol.upper())
            .order_by(MarketData.time.asc())
        )

        result = await self._session.execute(query)
        db_points = result.scalars().all()

        if not db_points:
            return None

        # Reconstruit la timeline depuis les données DB
        timeline = MarketDataTimeline(
            symbol=symbol.upper(),
            currency=self._get_currency_from_symbol(symbol),  # TODO: implémenter
        )

        points = [self._db_to_timeline_point(db_point) for db_point in db_points]
        timeline.add_points(points)

        return timeline

    async def save_timeline(self, timeline: MarketDataTimeline) -> MarketDataTimeline:
        """Sauvegarde une timeline complète"""
        # Sauvegarde tous les points modifiés
        if timeline._is_dirty:
            points_to_save = list(timeline._points.values())
            await self.bulk_save_points(timeline.symbol, points_to_save)
            timeline._is_dirty = False

        return timeline

    async def get_points_in_range(
        self,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        interval_type: Optional[IntervalType] = None,
    ) -> List[TimelinePoint]:
        """Récupère les points dans une plage temporelle"""
        conditions = [
            MarketData.symbol == symbol.upper(),
            MarketData.time >= start_time,
            MarketData.time <= end_time,
        ]

        if interval_type:
            conditions.append(MarketData.interval_type == interval_type.value)

        query = (
            select(MarketData).where(and_(*conditions)).order_by(MarketData.time.asc())
        )

        result = await self._session.execute(query)
        db_points = result.scalars().all()

        return [self._db_to_timeline_point(db_point) for db_point in db_points]

    async def get_latest_point(
        self, symbol: str, interval_type: IntervalType
    ) -> Optional[TimelinePoint]:
        """Récupère le point le plus récent"""
        query = (
            select(MarketData)
            .where(
                and_(
                    MarketData.symbol == symbol.upper(),
                    MarketData.interval_type == interval_type.value,
                )
            )
            .order_by(desc(MarketData.time))
            .limit(1)
        )

        result = await self._session.execute(query)
        db_point = result.scalar_one_or_none()

        if db_point:
            return self._db_to_timeline_point(db_point)
        return None

    async def bulk_save_points(self, symbol: str, points: List[TimelinePoint]) -> int:
        """Sauvegarde en lot optimisée pour TimescaleDB"""
        if not points:
            return 0

        saved_count = 0

        for point in points:
            db_point = self._timeline_point_to_db(symbol, point)

            # Utilise merge pour gérer les doublons
            try:
                merged = await self._session.merge(db_point)
                if merged:
                    saved_count += 1
            except IntegrityError:
                # Point déjà existant avec la même clé primaire
                await self._session.rollback()
                continue

        await self._session.flush()
        return saved_count

    async def delete_old_points(
        self,
        symbol: str,
        older_than: datetime,
        precision_level: Optional[PrecisionLevel] = None,
    ) -> int:
        """Supprime les anciens points"""
        conditions = [MarketData.symbol == symbol.upper(), MarketData.time < older_than]

        # TODO: Ajouter filtre sur precision_level quand disponible dans le modèle

        # Pour TimescaleDB, utilise DELETE avec condition sur time
        delete_query = MarketData.__table__.delete().where(and_(*conditions))

        result = await self._session.execute(delete_query)
        await self._session.flush()

        return result.rowcount if result.rowcount else 0

    async def get_timeline_stats(self, symbol: str) -> Dict[str, any]:
        """Statistiques sur la timeline d'un symbole"""
        # Requête agrégée optimisée
        stats_query = select(
            func.count(MarketData.time).label("total_points"),
            func.min(MarketData.time).label("oldest_point"),
            func.max(MarketData.time).label("newest_point"),
            func.count(func.distinct(MarketData.interval_type)).label("interval_types"),
        ).where(MarketData.symbol == symbol.upper())

        result = await self._session.execute(stats_query)
        stats = result.one()

        return {
            "total_points": stats.total_points or 0,
            "oldest_point": stats.oldest_point,
            "newest_point": stats.newest_point,
            "interval_types_count": stats.interval_types or 0,
        }

    async def get_symbols_with_data(
        self, min_points: int = 1, since: Optional[datetime] = None
    ) -> List[str]:
        """Retourne les symboles ayant des données"""
        conditions = []

        if since:
            conditions.append(MarketData.time >= since)

        query = (
            select(MarketData.symbol)
            .where(and_(*conditions) if conditions else True)
            .group_by(MarketData.symbol)
            .having(func.count(MarketData.time) >= min_points)
            .order_by(MarketData.symbol)
        )

        result = await self._session.execute(query)
        return [row[0] for row in result.fetchall()]

    def _db_to_timeline_point(self, db_point: MarketData) -> TimelinePoint:
        """Convertit un objet DB en TimelinePoint"""
        from decimal import Decimal

        # TODO: Récupérer la vraie currency depuis la configuration
        currency = self._get_currency_from_symbol(db_point.symbol)

        return TimelinePoint(
            timestamp=db_point.time,
            open_price=self._create_money(db_point.open_price, currency),
            high_price=self._create_money(db_point.high_price, currency),
            low_price=self._create_money(db_point.low_price, currency),
            close_price=self._create_money(db_point.close_price, currency),
            adjusted_close=self._create_money(db_point.adjusted_close, currency),
            volume=db_point.volume or 0,
            interval_type=IntervalType(db_point.interval_type),
            source=DataSource(db_point.source)
            if db_point.source
            else DataSource.YFINANCE,
            precision_level=self._determine_precision_level(db_point.time),
            created_at=db_point.created_at or datetime.now(timezone.utc),
        )

    def _timeline_point_to_db(self, symbol: str, point: TimelinePoint) -> MarketData:
        """Convertit un TimelinePoint en objet DB"""
        return MarketData(
            time=point.timestamp,
            symbol=symbol.upper(),
            interval_type=point.interval_type.value,
            open_price=point.open_price.amount,
            high_price=point.high_price.amount,
            low_price=point.low_price.amount,
            close_price=point.close_price.amount,
            adjusted_close=point.adjusted_close.amount,
            volume=point.volume,
            source=point.source.value,
            created_at=point.created_at,
        )

    def _get_currency_from_symbol(self, symbol: str):
        """Détermine la currency d'un symbole (temporaire)"""
        from ..entities.market_data_timeline import Currency

        # Logique simplifiée - à améliorer avec une vraie base de données des symboles
        if any(suffix in symbol.upper() for suffix in [".TO", ".V"]):
            return Currency(code="CAD", name="Canadian Dollar", symbol="$")
        elif any(suffix in symbol.upper() for suffix in [".L", ".LON"]):
            return Currency(code="GBP", name="British Pound", symbol="£")
        elif any(suffix in symbol.upper() for suffix in [".PA", ".F"]):
            return Currency(code="EUR", name="Euro", symbol="€")
        else:
            return Currency(code="USD", name="US Dollar", symbol="$")

    def _create_money(self, amount, currency):
        """Crée un objet Money"""
        from decimal import Decimal

        from ..entities.market_data_timeline import Money

        if amount is None:
            amount = Decimal("0")
        elif not isinstance(amount, Decimal):
            amount = Decimal(str(amount))

        return Money(amount=amount, currency=currency)

    def _determine_precision_level(self, timestamp: datetime) -> PrecisionLevel:
        """Détermine le niveau de précision basé sur l'âge"""
        now = datetime.now(timezone.utc)
        age_hours = (now - timestamp).total_seconds() / 3600

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


class MarketDataTimelineSpecification:
    """Spécifications pour requêtes complexes sur les timelines"""

    @staticmethod
    def symbol_equals(symbol: str):
        """Spécification: symbole égal"""
        return MarketData.symbol == symbol.upper()

    @staticmethod
    def time_range(start: datetime, end: datetime):
        """Spécification: plage temporelle"""
        return and_(MarketData.time >= start, MarketData.time <= end)

    @staticmethod
    def interval_type_in(intervals: List[IntervalType]):
        """Spécification: type d'intervalle"""
        return MarketData.interval_type.in_([i.value for i in intervals])

    @staticmethod
    def recent_data(hours: int = 24):
        """Spécification: données récentes"""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        return MarketData.time >= cutoff

    @staticmethod
    def high_volume(min_volume: int = 1000000):
        """Spécification: volume élevé"""
        return MarketData.volume >= min_volume

    @staticmethod
    def significant_movement(min_change_percent: float = 5.0):
        """Spécification: mouvement significatif"""
        return (
            func.abs(
                (MarketData.close_price - MarketData.open_price)
                / MarketData.open_price
                * 100
            )
            >= min_change_percent
        )


# Factory pour créer les repositories
class RepositoryFactory:
    """Factory pour créer les repositories"""

    @staticmethod
    def create_timeline_repository(
        session: AsyncSession,
    ) -> IMarketDataTimelineRepository:
        """Crée un repository de timeline"""
        return SqlAlchemyMarketDataTimelineRepository(session)
