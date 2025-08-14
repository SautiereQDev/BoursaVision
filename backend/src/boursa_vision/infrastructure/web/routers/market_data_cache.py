"""
API Router pour le Cache Intelligent YFinance
============================================

Endpoints FastAPI pour interagir avec le système de cache intelligent
des données de marché YFinance.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from ...application.services.market_data_cache_service import MarketDataCacheService
from ...domain.entities.market_data_timeline import IntervalType, PrecisionLevel

logger = logging.getLogger(__name__)


# Modèles Pydantic pour les requêtes/réponses
class MarketDataRequest(BaseModel):
    """Requête pour récupérer des données de marché"""

    symbol: str = Field(..., description="Symbole boursier", example="AAPL")
    start_date: Optional[datetime] = Field(None, description="Date de début")
    end_date: Optional[datetime] = Field(None, description="Date de fin")
    interval: str = Field("1d", description="Intervalle des données", example="1d")
    max_age_hours: float = Field(1.0, description="Âge maximum des données en heures")
    force_refresh: bool = Field(False, description="Forcer le rafraîchissement")

    @validator("symbol")
    def validate_symbol(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Symbol cannot be empty")
        return v.upper().strip()

    @validator("interval")
    def validate_interval(cls, v):
        valid_intervals = [
            "1m",
            "2m",
            "5m",
            "15m",
            "30m",
            "60m",
            "90m",
            "1d",
            "5d",
            "1wk",
            "1mo",
            "3mo",
        ]
        if v not in valid_intervals:
            raise ValueError(f"Invalid interval. Must be one of: {valid_intervals}")
        return v


class MarketDataPoint(BaseModel):
    """Point de données de marché"""

    timestamp: datetime
    open_price: float
    high_price: float
    low_price: float
    close_price: float
    adjusted_close: float
    volume: int
    interval_type: str
    source: str
    precision_level: str
    price_change_percent: float


class MarketDataResponse(BaseModel):
    """Réponse des données de marché"""

    symbol: str
    interval: str
    total_points: int
    data_range: Dict[str, Optional[datetime]]
    cache_info: Dict[str, Any]
    points: List[MarketDataPoint]


class TimelineMetricsResponse(BaseModel):
    """Métriques de qualité d'une timeline"""

    symbol: str
    total_points: int
    data_coverage_percent: float
    gaps_count: int
    significant_gaps_count: int
    data_quality_score: float
    oldest_point: Optional[datetime]
    newest_point: Optional[datetime]
    precision_distribution: Dict[str, int]


class CacheStatsResponse(BaseModel):
    """Statistiques du cache"""

    service_stats: Dict[str, Any]
    cache_manager_stats: Dict[str, Any]
    timelines_in_memory: int
    total_requests: int
    cache_hit_rate: float
    performance_metrics: Dict[str, Any]


class BulkRefreshRequest(BaseModel):
    """Requête pour rafraîchissement en lot"""

    symbols: List[str] = Field(..., description="Liste des symboles à rafraîchir")
    interval: str = Field("1d", description="Intervalle des données")
    max_concurrent: int = Field(
        10, description="Nombre maximum de requêtes simultanées"
    )

    @validator("symbols")
    def validate_symbols(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Symbols list cannot be empty")
        return [s.upper().strip() for s in v if s.strip()]


class BulkRefreshResponse(BaseModel):
    """Réponse du rafraîchissement en lot"""

    total_symbols: int
    successful_refreshes: int
    failed_refreshes: int
    results: Dict[str, bool]
    duration_seconds: float


# Router pour les endpoints de cache
router = APIRouter(
    prefix="/api/v1/cache",
    tags=["Cache de Données YFinance"],
    responses={404: {"description": "Ressource non trouvée"}},
)


# Dépendance pour injecter le service de cache
async def get_cache_service() -> MarketDataCacheService:
    """Factory pour le service de cache - à remplacer par l'injection de dépendance"""
    # TODO: Implémenter l'injection de dépendance propre
    from ...domain.services.cache_strategies import CacheConfig

    config = CacheConfig()
    return MarketDataCacheService(cache_config=config)


@router.get("/market-data/{symbol}", response_model=MarketDataResponse)
async def get_market_data(
    symbol: str,
    start_date: Optional[str] = Query(None, description="Date de début (ISO format)"),
    end_date: Optional[str] = Query(None, description="Date de fin (ISO format)"),
    interval: str = Query("1d", description="Intervalle des données"),
    max_age_hours: float = Query(1.0, description="Âge maximum en heures"),
    force_refresh: bool = Query(False, description="Forcer le rafraîchissement"),
    cache_service: MarketDataCacheService = Depends(get_cache_service),
) -> MarketDataResponse:
    """
    Récupère les données de marché pour un symbole avec cache intelligent.

    Le système de cache optimise automatiquement la récupération selon :
    - L'âge des données demandées
    - La fréquence d'accès du symbole
    - La précision requise selon l'intervalle temporel
    """
    try:
        # Validation et conversion des paramètres
        symbol = symbol.upper().strip()

        # Conversion des dates
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        # Conversion de l'intervalle
        interval_mapping = {
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

        interval_enum = interval_mapping.get(interval, IntervalType.ONE_DAY)

        # Récupération des données via le cache intelligent
        points = await cache_service.get_market_data(
            symbol=symbol,
            start_time=start_dt,
            end_time=end_dt,
            interval=interval_enum,
            max_age_hours=max_age_hours,
        )

        # Conversion en modèles Pydantic
        response_points = []
        for point in points:
            response_points.append(
                MarketDataPoint(
                    timestamp=point.timestamp,
                    open_price=float(point.open_price.amount),
                    high_price=float(point.high_price.amount),
                    low_price=float(point.low_price.amount),
                    close_price=float(point.close_price.amount),
                    adjusted_close=float(point.adjusted_close.amount),
                    volume=point.volume,
                    interval_type=point.interval_type.value,
                    source=point.source.value,
                    precision_level=point.precision_level.value,
                    price_change_percent=point.price_change_percent,
                )
            )

        # Calcul des informations de plage
        data_range = {
            "start": points[0].timestamp if points else None,
            "end": points[-1].timestamp if points else None,
        }

        # Informations de cache
        cache_stats = cache_service.get_cache_stats()

        return MarketDataResponse(
            symbol=symbol,
            interval=interval,
            total_points=len(points),
            data_range=data_range,
            cache_info={
                "cache_hit_rate": cache_stats["cache_hit_rate"],
                "total_requests": cache_stats["total_requests"],
                "timelines_in_memory": cache_stats["timelines_in_memory"],
            },
            points=response_points,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Paramètres invalides: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des données pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de la récupération des données",
        )


@router.get("/timeline-metrics/{symbol}", response_model=TimelineMetricsResponse)
async def get_timeline_metrics(
    symbol: str, cache_service: MarketDataCacheService = Depends(get_cache_service)
) -> TimelineMetricsResponse:
    """Récupère les métriques de qualité d'une timeline"""
    try:
        symbol = symbol.upper().strip()

        # Récupère la timeline
        timeline = await cache_service.get_timeline(symbol)
        if not timeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Timeline non trouvée pour le symbole {symbol}",
            )

        # Calcule les métriques
        metrics = timeline.get_metrics()

        return TimelineMetricsResponse(
            symbol=symbol,
            total_points=metrics.total_points,
            data_coverage_percent=metrics.data_coverage_percent,
            gaps_count=metrics.gaps_count,
            significant_gaps_count=metrics.significant_gaps_count,
            data_quality_score=metrics.data_quality_score,
            oldest_point=metrics.oldest_point,
            newest_point=metrics.newest_point,
            precision_distribution={
                k.value: v for k, v in metrics.precision_distribution.items()
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors du calcul des métriques pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors du calcul des métriques",
        )


@router.post("/bulk-refresh", response_model=BulkRefreshResponse)
async def bulk_refresh_symbols(
    request: BulkRefreshRequest,
    cache_service: MarketDataCacheService = Depends(get_cache_service),
) -> BulkRefreshResponse:
    """Rafraîchit plusieurs symboles en parallèle"""
    try:
        start_time = datetime.now()

        # Conversion de l'intervalle
        interval_mapping = {
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

        interval_enum = interval_mapping.get(request.interval, IntervalType.ONE_DAY)

        # Rafraîchissement en parallèle
        results = await cache_service.bulk_refresh_symbols(
            symbols=request.symbols,
            interval=interval_enum,
            max_concurrent=request.max_concurrent,
        )

        # Calcul des statistiques
        successful = sum(1 for success in results.values() if success)
        failed = len(results) - successful
        duration = (datetime.now() - start_time).total_seconds()

        return BulkRefreshResponse(
            total_symbols=len(request.symbols),
            successful_refreshes=successful,
            failed_refreshes=failed,
            results=results,
            duration_seconds=duration,
        )

    except Exception as e:
        logger.error(f"Erreur lors du rafraîchissement en lot: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors du rafraîchissement",
        )


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_statistics(
    cache_service: MarketDataCacheService = Depends(get_cache_service),
) -> CacheStatsResponse:
    """Récupère les statistiques détaillées du cache"""
    try:
        stats = cache_service.get_cache_stats()

        # Calcul de métriques de performance additionnelles
        performance_metrics = {
            "efficiency_score": (
                stats["cache_hit_rate"] * 0.6
                + (100 - stats["service_stats"]["yfinance_requests"]) * 0.4
            ),
            "data_freshness": "optimal"
            if stats["cache_hit_rate"] > 80
            else "suboptimal",
            "memory_efficiency": stats["timelines_in_memory"]
            / max(1, stats["total_requests"])
            * 100,
        }

        return CacheStatsResponse(
            service_stats=stats["service_stats"],
            cache_manager_stats=stats["cache_manager_stats"],
            timelines_in_memory=stats["timelines_in_memory"],
            total_requests=stats["total_requests"],
            cache_hit_rate=stats["cache_hit_rate"],
            performance_metrics=performance_metrics,
        )

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des statistiques: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de la récupération des statistiques",
        )


@router.delete("/clear/{symbol}")
async def clear_symbol_cache(
    symbol: str, cache_service: MarketDataCacheService = Depends(get_cache_service)
) -> JSONResponse:
    """Vide le cache pour un symbole spécifique"""
    try:
        symbol = symbol.upper().strip()
        cache_service.clear_cache(symbol)

        return JSONResponse(
            content={
                "message": f"Cache vidé pour le symbole {symbol}",
                "symbol": symbol,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Erreur lors du vidage du cache pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors du vidage du cache",
        )


@router.delete("/clear-all")
async def clear_all_cache(
    cache_service: MarketDataCacheService = Depends(get_cache_service),
) -> JSONResponse:
    """Vide tout le cache"""
    try:
        cache_service.clear_cache()

        return JSONResponse(
            content={
                "message": "Cache entièrement vidé",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Erreur lors du vidage complet du cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors du vidage du cache",
        )


@router.get("/latest-price/{symbol}")
async def get_latest_price(
    symbol: str, cache_service: MarketDataCacheService = Depends(get_cache_service)
) -> JSONResponse:
    """Récupère le dernier prix d'un symbole"""
    try:
        symbol = symbol.upper().strip()

        latest_price = await cache_service.get_latest_price(symbol)
        if not latest_price:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Aucun prix trouvé pour le symbole {symbol}",
            )

        return JSONResponse(
            content={
                "symbol": symbol,
                "price": float(latest_price.amount),
                "currency": latest_price.currency.code,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération du prix pour {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur interne lors de la récupération du prix",
        )
