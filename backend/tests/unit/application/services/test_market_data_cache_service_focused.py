"""
Tests ciblés pour MarketDataCacheService - Focus sur les vraies méthodes
========================================================================

Tests concentrés sur l'API réelle du service pour maximiser la couverture
avec un minimum de complexité.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest

from boursa_vision.application.services.market_data_cache_service import (
    MarketDataCacheService,
    YFinanceDataFetcher,
)
from boursa_vision.domain.entities.market_data_timeline import (
    Currency,
    DataSource,
    IntervalType,
    MarketDataTimeline,
    Money,
    PrecisionLevel,
    TimelinePoint,
)
from boursa_vision.domain.services.cache_strategies import CacheConfig


class TestMarketDataCacheServiceBasics:
    """Tests de base pour MarketDataCacheService"""

    def test_init_default(self):
        """Test initialisation avec paramètres par défaut"""
        service = MarketDataCacheService()

        assert service.cache_config is not None
        assert service.cache_manager is not None
        assert service.fetcher is not None
        assert service._timelines == {}
        assert service.stats["cache_hits"] == 0

    def test_init_with_repository(self):
        """Test initialisation avec repository"""
        mock_repo = Mock()
        service = MarketDataCacheService(timeline_repository=mock_repo)

        assert service.timeline_repository == mock_repo

    @pytest.mark.asyncio
    async def test_get_timeline_new_symbol(self):
        """Test création d'une nouvelle timeline"""
        service = MarketDataCacheService()

        timeline = await service.get_timeline("AAPL")

        assert timeline is not None
        assert timeline.symbol == "AAPL"
        assert "AAPL" in service._timelines
        assert service.stats["timelines_loaded"] == 1

    @pytest.mark.asyncio
    async def test_get_timeline_memory_cache_hit(self):
        """Test hit du cache mémoire"""
        service = MarketDataCacheService()

        # Premier appel
        timeline1 = await service.get_timeline("MSFT")
        # Deuxième appel
        timeline2 = await service.get_timeline("MSFT")

        assert timeline1 is timeline2
        assert service.stats["timelines_loaded"] == 1

    @pytest.mark.asyncio
    async def test_get_timeline_force_refresh(self):
        """Test force refresh ignore le cache"""
        service = MarketDataCacheService()

        # Premier appel
        await service.get_timeline("GOOGL")

        # Force refresh
        timeline = await service.get_timeline("GOOGL", force_refresh=True)

        assert timeline is not None

    def test_get_cache_stats_basic(self):
        """Test récupération des statistiques de base"""
        service = MarketDataCacheService()
        service.stats["cache_hits"] = 5
        service.stats["cache_misses"] = 3
        service.cache_manager.get_stats = Mock(return_value={"entries": 10})

        stats = service.get_cache_stats()

        assert stats["service_stats"]["cache_hits"] == 5
        assert stats["service_stats"]["cache_misses"] == 3
        assert stats["total_requests"] == 8
        assert "cache_hit_rate" in stats

    def test_clear_cache_all(self):
        """Test vidage complet du cache"""
        service = MarketDataCacheService()
        service._timelines["TEST1"] = Mock()
        service._timelines["TEST2"] = Mock()
        service.cache_manager.clear_all = Mock()

        service.clear_cache()

        assert len(service._timelines) == 0
        service.cache_manager.clear_all.assert_called_once()

    def test_clear_cache_specific_symbol(self):
        """Test vidage pour un symbole spécifique"""
        service = MarketDataCacheService()
        service._timelines["KEEP"] = Mock()
        service._timelines["DELETE"] = Mock()
        service.cache_manager.clear_symbol = Mock()

        service.clear_cache("DELETE")

        assert "KEEP" in service._timelines
        assert "DELETE" not in service._timelines
        service.cache_manager.clear_symbol.assert_called_once_with("DELETE")

    @pytest.mark.asyncio
    async def test_get_latest_price_exists(self):
        """Test récupération du dernier prix"""
        service = MarketDataCacheService()
        mock_timeline = Mock()
        mock_price = Money(
            Decimal("100.0"), Currency(code="USD", name="US Dollar", symbol="$")
        )
        mock_timeline.get_latest_price.return_value = mock_price
        service._timelines["PRICE_TEST"] = mock_timeline

        result = await service.get_latest_price("PRICE_TEST")

        assert result == mock_price

    @pytest.mark.asyncio
    async def test_get_latest_price_no_timeline(self):
        """Test prix quand pas de timeline"""
        service = MarketDataCacheService()

        result = await service.get_latest_price("NO_EXIST")

        assert result is None


class TestYFinanceDataFetcher:
    """Tests pour YFinanceDataFetcher"""

    def test_init(self):
        """Test initialisation du fetcher"""
        fetcher = YFinanceDataFetcher()

        assert fetcher.request_count == 0
        assert fetcher.last_request_time is None
        assert (
            abs(fetcher.rate_limit_delay - 0.1) < 0.01
        )  # Use approximate equality for floats

    def test_get_currency_for_symbol_us(self):
        """Test détection currency pour symboles US"""
        fetcher = YFinanceDataFetcher()

        currency = fetcher._get_currency_for_symbol("AAPL")

        assert currency.code == "USD"

    def test_get_currency_for_symbol_canadian(self):
        """Test détection currency pour symboles canadiens"""
        fetcher = YFinanceDataFetcher()

        currency = fetcher._get_currency_for_symbol("SHOP.TO")

        assert currency.code == "CAD"

    def test_yf_interval_to_enum(self):
        """Test conversion des intervalles YFinance"""
        fetcher = YFinanceDataFetcher()

        assert fetcher._yf_interval_to_enum("1d") == IntervalType.ONE_DAY
        assert fetcher._yf_interval_to_enum("1m") == IntervalType.ONE_MINUTE
        assert fetcher._yf_interval_to_enum("1wk") == IntervalType.ONE_WEEK

    def test_get_precision_for_age(self):
        """Test calcul de précision selon l'âge"""
        fetcher = YFinanceDataFetcher()

        # Données récentes
        assert fetcher._get_precision_for_age(1) == PrecisionLevel.ULTRA_HIGH
        # Données d'une semaine
        assert fetcher._get_precision_for_age(100) == PrecisionLevel.HIGH
        # Données très anciennes
        assert fetcher._get_precision_for_age(10000) == PrecisionLevel.VERY_LOW

    @pytest.mark.asyncio
    async def test_fetch_historical_data_mock_fallback(self):
        """Test génération de données mock quand YFinance non disponible"""
        fetcher = YFinanceDataFetcher()

        with patch(
            "boursa_vision.application.services.market_data_cache_service.YF_AVAILABLE",
            False,
        ):
            points = await fetcher.fetch_historical_data("TEST_SYMBOL", "1y", "1d")

        assert len(points) == 30  # 30 jours de mock data
        assert all(isinstance(point, TimelinePoint) for point in points)
        assert all(point.source == DataSource.YFINANCE for point in points)


class TestMarketDataCacheServiceIntegration:
    """Tests d'intégration pour MarketDataCacheService"""

    @pytest.mark.asyncio
    async def test_get_market_data_basic_flow(self):
        """Test du flux basique de get_market_data"""
        service = MarketDataCacheService()

        # Mock le fetcher pour retourner des données
        mock_points = [
            TimelinePoint(
                timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
                open_price=Money(
                    Decimal("100.0"), Currency(code="USD", name="US Dollar", symbol="$")
                ),
                high_price=Money(
                    Decimal("105.0"), Currency(code="USD", name="US Dollar", symbol="$")
                ),
                low_price=Money(
                    Decimal("99.0"), Currency(code="USD", name="US Dollar", symbol="$")
                ),
                close_price=Money(
                    Decimal("104.0"), Currency(code="USD", name="US Dollar", symbol="$")
                ),
                adjusted_close=Money(
                    Decimal("104.0"), Currency(code="USD", name="US Dollar", symbol="$")
                ),
                volume=1000000,
                interval_type=IntervalType.ONE_DAY,
                source=DataSource.YFINANCE,
                precision_level=PrecisionLevel.HIGH,
            )
        ]

        with patch.object(
            service.fetcher, "fetch_historical_data", return_value=mock_points
        ):
            result = await service.get_market_data("TEST_INTEGRATION")

        assert len(result) <= len(mock_points)  # Peut être filtré par range
        assert service.stats["yfinance_requests"] >= 1

    @pytest.mark.asyncio
    async def test_bulk_refresh_symbols_basic(self):
        """Test du bulk refresh de base"""
        service = MarketDataCacheService()
        symbols = ["BULK1", "BULK2"]

        with patch.object(service, "_refresh_timeline_data", return_value=None):
            with patch.object(service, "get_timeline") as mock_get_timeline:
                mock_timeline = Mock()
                mock_timeline.needs_refresh.return_value = True
                mock_get_timeline.return_value = mock_timeline

                results = await service.bulk_refresh_symbols(symbols, max_concurrent=2)

        assert len(results) == 2
        assert all(symbol in results for symbol in symbols)

    @pytest.mark.asyncio
    async def test_cleanup_old_data_with_repository(self):
        """Test cleanup avec repository"""
        service = MarketDataCacheService()
        service.timeline_repository = AsyncMock()
        service.timeline_repository.delete_old_points = AsyncMock(return_value=5)

        # Ajouter une timeline en mémoire
        timeline = MarketDataTimeline(
            symbol="CLEANUP_TEST",
            currency=Currency(code="USD", name="US Dollar", symbol="$"),
        )
        service._timelines["CLEANUP_TEST"] = timeline

        result = await service.cleanup_old_data(older_than_days=30)

        assert len(result) > 0
        service.timeline_repository.delete_old_points.assert_called()

    @pytest.mark.asyncio
    async def test_cleanup_old_data_no_repository(self):
        """Test cleanup sans repository"""
        service = MarketDataCacheService(timeline_repository=None)

        result = await service.cleanup_old_data()

        assert result == {}

    def test_determine_yfinance_params(self):
        """Test détermination des paramètres YFinance"""
        service = MarketDataCacheService()

        start_time = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 2, tzinfo=timezone.utc)  # 1 jour

        period, interval = service._determine_yfinance_params(
            start_time, end_time, IntervalType.ONE_DAY
        )

        assert period == "1d"
        assert interval == "1d"

    @pytest.mark.asyncio
    async def test_get_timeline_with_database_success(self):
        """Test chargement timeline depuis la base de données"""
        mock_repo = AsyncMock()
        mock_timeline = MarketDataTimeline(
            symbol="DB_TEST",
            currency=Currency(code="USD", name="US Dollar", symbol="$"),
        )
        mock_repo.get_timeline.return_value = mock_timeline

        service = MarketDataCacheService(timeline_repository=mock_repo)

        result = await service.get_timeline("DB_TEST")

        assert result == mock_timeline
        assert service.stats["db_reads"] == 1
        mock_repo.get_timeline.assert_called_once_with("DB_TEST")

    @pytest.mark.asyncio
    async def test_get_timeline_database_exception(self):
        """Test gestion d'exception lors du chargement DB"""
        mock_repo = AsyncMock()
        mock_repo.get_timeline.side_effect = Exception("DB Error")

        service = MarketDataCacheService(timeline_repository=mock_repo)

        # Ne doit pas lever d'exception, doit créer une nouvelle timeline
        result = await service.get_timeline("ERROR_TEST")

        assert result is not None
        assert result.symbol == "ERROR_TEST"
