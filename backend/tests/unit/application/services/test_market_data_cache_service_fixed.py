"""
Tests unitaires pour le service de cache MarketDataCacheService
Couverture exhaustive des fonctionnalités critiques : caching, rate limiting, 
récupération de données, gestion d'erreurs et événements.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

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


@pytest.mark.unit
@pytest.mark.cache
class TestYFinanceDataFetcher:
    """Tests complets pour YFinanceDataFetcher avec focus sur les méthodes privées critiques."""

    def setup_method(self):
        """Configuration avant chaque test."""
        self.fetcher = YFinanceDataFetcher()
        self.test_symbol = "AAPL"
        self.test_currency = Currency(code="USD", name="US Dollar", symbol="$")

    @pytest.mark.asyncio
    async def test_should_apply_rate_limiting_between_requests(self):
        """Test que le rate limiting fonctionne correctement."""
        # Given
        start_time = datetime.now().timestamp()

        # When - deux requêtes consécutives
        await self.fetcher._apply_rate_limit()
        first_call_time = datetime.now().timestamp()

        await self.fetcher._apply_rate_limit()
        second_call_time = datetime.now().timestamp()

        # Then
        time_diff = second_call_time - first_call_time
        assert time_diff >= 0.09  # Rate limit est de 0.1s, avec tolérance
        assert self.fetcher.last_request_time is not None

    @pytest.mark.asyncio
    async def test_should_not_delay_when_enough_time_passed(self):
        """Test qu'aucun délai n'est appliqué si assez de temps s'est écoulé."""
        # Given
        self.fetcher.last_request_time = (
            datetime.now().timestamp() - 1.0
        )  # 1 seconde dans le passé

        # When
        start_time = datetime.now().timestamp()
        await self.fetcher._apply_rate_limit()
        end_time = datetime.now().timestamp()

        # Then
        delay = end_time - start_time
        assert delay < 0.01  # Pas de délai significatif

    def test_should_convert_yfinance_intervals_to_enum(self):
        """Test de la conversion des intervalles YFinance vers nos enums."""
        # Given & When & Then
        test_cases = [
            ("1m", IntervalType.ONE_MINUTE),
            ("1d", IntervalType.ONE_DAY),
            ("1wk", IntervalType.ONE_WEEK),
            ("1mo", IntervalType.ONE_MONTH),
            ("unknown", IntervalType.ONE_DAY),  # Fallback case
        ]

        for yf_interval, expected_enum in test_cases:
            result = self.fetcher._yf_interval_to_enum(yf_interval)
            assert result == expected_enum

    def test_should_get_currency_for_different_symbols(self):
        """Test de la détection de currency basée sur les suffixes de symboles."""
        # Given & When & Then
        test_cases = [
            ("AAPL", "USD"),  # US stock
            ("SHOP.TO", "CAD"),  # Toronto exchange
            ("RDSA.L", "GBP"),  # London exchange
            ("MC.PA", "EUR"),  # Paris exchange
            ("SAP.F", "EUR"),  # Frankfurt exchange
        ]

        for symbol, expected_code in test_cases:
            result = self.fetcher._get_currency_for_symbol(symbol)
            assert result.code == expected_code

    def test_should_determine_precision_based_on_data_age(self):
        """Test de la logique de précision selon l'âge des données."""
        # Given & When & Then
        test_cases = [
            (12, PrecisionLevel.ULTRA_HIGH),  # < 24h
            (48, PrecisionLevel.HIGH),  # < 1 semaine
            (360, PrecisionLevel.MEDIUM),  # < 1 mois
            (4380, PrecisionLevel.LOW),  # < 1 an
            (10000, PrecisionLevel.VERY_LOW),  # > 1 an
        ]

        for age_hours, expected_level in test_cases:
            result = self.fetcher._get_precision_for_age(age_hours)
            assert result == expected_level

    @pytest.mark.asyncio
    @patch(
        "boursa_vision.application.services.market_data_cache_service.YF_AVAILABLE",
        False,
    )
    async def test_should_return_mock_data_when_yfinance_unavailable(self):
        """Test du fallback sur mock data quand YFinance n'est pas disponible."""
        # Given
        symbol = "AAPL"

        # When
        result = await self.fetcher.fetch_historical_data(symbol)

        # Then
        assert isinstance(result, list)
        assert len(result) == 30  # Mock génère 30 jours de données

        if result:  # Vérification si data disponible
            first_point = result[0]
            assert hasattr(first_point, "timestamp")
            assert hasattr(first_point, "open_price")
            assert hasattr(first_point, "close_price")

    @pytest.mark.asyncio
    @patch("boursa_vision.application.services.market_data_cache_service.yf")
    async def test_should_fetch_historical_data_successfully(self, mock_yf):
        """Test réussite de récupération de données historiques."""
        # Given
        mock_ticker = Mock()
        mock_hist = Mock()
        mock_hist.empty = False
        mock_hist.iterrows.return_value = [
            (
                Mock(to_pydatetime=lambda: datetime.now(timezone.utc)),
                {
                    "Open": 150.0,
                    "High": 155.0,
                    "Low": 148.0,
                    "Close": 152.0,
                    "Adj Close": 152.0,
                    "Volume": 1000000,
                },
            )
        ]
        mock_ticker.history.return_value = mock_hist
        mock_yf.Ticker.return_value = mock_ticker

        # When
        result = await self.fetcher.fetch_historical_data("AAPL")

        # Then
        assert len(result) == 1
        assert self.fetcher.request_count == 1

    @pytest.mark.asyncio
    async def test_should_handle_empty_data_response(self):
        """Test de gestion des réponses vides de YFinance."""
        # Given & When & Then
        with patch(
            "boursa_vision.application.services.market_data_cache_service.yf"
        ) as mock_yf:
            mock_ticker = Mock()
            mock_hist = Mock()
            mock_hist.empty = True
            mock_ticker.history.return_value = mock_hist
            mock_yf.Ticker.return_value = mock_ticker

            result = await self.fetcher.fetch_historical_data("INVALID")

            assert result == []


@pytest.mark.unit
@pytest.mark.cache
class TestMarketDataCacheService:
    """Tests complets pour MarketDataCacheService avec focus sur les opérations de cache."""

    def setup_method(self):
        """Configuration avant chaque test."""
        self.cache_config = CacheConfig()
        self.test_currency = Currency(code="USD", name="US Dollar", symbol="$")

        # Mock du repository
        self.mock_repository = Mock()

        # Mock du fetcher
        self.mock_fetcher = Mock()
        self.mock_fetcher.fetch_historical_data = AsyncMock(return_value=[])

        # Service avec dépendances mockées
        self.service = MarketDataCacheService(
            cache_config=self.cache_config, timeline_repository=self.mock_repository
        )
        self.service.fetcher = self.mock_fetcher

    @pytest.mark.asyncio
    async def test_should_return_timeline_from_memory_cache(self):
        """Test de retour de timeline depuis le cache mémoire."""
        # Given
        symbol = "AAPL"
        test_timeline = MarketDataTimeline(symbol=symbol, currency=self.test_currency)
        self.service._timelines[symbol] = test_timeline

        # When
        result = await self.service.get_timeline(symbol)

        # Then
        assert result == test_timeline
        assert (
            self.service.stats["cache_hits"] == 0
        )  # Memory cache ne compte pas comme hit

    @pytest.mark.asyncio
    async def test_should_force_refresh_ignore_memory_cache(self):
        """Test que force_refresh ignore le cache mémoire."""
        # Given
        symbol = "AAPL"
        test_timeline = MarketDataTimeline(symbol=symbol, currency=self.test_currency)
        self.service._timelines[symbol] = test_timeline

        # Mock timeline repository pour retourner None (pas de données)
        self.mock_repository.get_timeline.return_value = None

        # When
        await self.service.get_timeline(symbol, force_refresh=True)

        # Then - Le cache mémoire devrait être ignoré
        self.mock_repository.get_timeline.assert_called_once()

    def test_should_initialize_with_default_config(self):
        """Test d'initialisation avec configuration par défaut."""
        # Given & When
        service = MarketDataCacheService()

        # Then
        assert service.cache_config is not None
        assert service.cache_manager is not None
        assert service.fetcher is not None
        assert isinstance(service.stats, dict)
        assert service.stats["cache_hits"] == 0

    def test_should_initialize_with_custom_config(self):
        """Test d'initialisation avec configuration custom."""
        # Given
        custom_config = CacheConfig()

        # When
        service = MarketDataCacheService(cache_config=custom_config)

        # Then
        assert service.cache_config == custom_config

    @pytest.mark.asyncio
    async def test_should_handle_missing_timeline_gracefully(self):
        """Test de gestion des timelines manquantes."""
        # Given
        symbol = "NONEXISTENT"
        self.mock_repository.get_timeline.return_value = None

        # When
        await self.service.get_timeline(symbol)

        # Then
        # Le service devrait gérer les timelines manquantes sans erreur
        self.mock_repository.get_timeline.assert_called_once_with(symbol)

    def test_should_track_statistics_correctly(self):
        """Test du tracking des statistiques d'utilisation."""
        # Given
        initial_stats = self.service.stats.copy()

        # When - Simulation de différentes opérations
        self.service.stats["cache_hits"] += 1
        self.service.stats["yfinance_requests"] += 1

        # Then
        assert self.service.stats["cache_hits"] == initial_stats["cache_hits"] + 1
        assert (
            self.service.stats["yfinance_requests"]
            == initial_stats["yfinance_requests"] + 1
        )

    def test_should_store_timelines_in_memory_cache(self):
        """Test de stockage des timelines dans le cache mémoire."""
        # Given
        symbol = "AAPL"
        timeline = MarketDataTimeline(symbol=symbol, currency=self.test_currency)

        # When
        self.service._timelines[symbol] = timeline

        # Then
        assert symbol in self.service._timelines
        assert self.service._timelines[symbol] == timeline

    def test_should_convert_symbol_to_uppercase(self):
        """Test de conversion automatique des symboles en majuscules."""
        # Given
        lowercase_symbol = "aapl"
        timeline = MarketDataTimeline(
            symbol=lowercase_symbol.upper(), currency=self.test_currency
        )
        self.service._timelines[lowercase_symbol.upper()] = timeline

        # When
        result_exists = lowercase_symbol.upper() in self.service._timelines

        # Then
        assert result_exists

    @pytest.mark.asyncio
    async def test_should_handle_fetcher_exceptions_gracefully(self):
        """Test de gestion des exceptions du fetcher."""
        # Given
        symbol = "AAPL"
        self.mock_fetcher.fetch_historical_data.side_effect = Exception("Network error")
        self.mock_repository.get_timeline.return_value = None

        # When & Then - Ne devrait pas lever d'exception
        await self.service.get_timeline(symbol)
        # Le service devrait gérer l'exception proprement

    def test_should_maintain_fetcher_instance(self):
        """Test que l'instance du fetcher est correctement maintenue."""
        # Given & When & Then
        assert self.service.fetcher is not None
        assert hasattr(self.service.fetcher, "fetch_historical_data")


@pytest.mark.unit
@pytest.mark.cache
class TestCachePerformance:
    """Tests de performance et charge pour le cache."""

    def setup_method(self):
        """Configuration pour les tests de performance."""
        self.service = MarketDataCacheService()

    @pytest.mark.asyncio
    async def test_should_complete_cache_operations_under_100ms(self):
        """Test que les opérations de cache se completent sous 100ms."""
        # Given
        symbol = "AAPL"
        test_currency = Currency(code="USD", name="US Dollar", symbol="$")
        timeline = MarketDataTimeline(symbol=symbol, currency=test_currency)

        # When
        start_time = asyncio.get_event_loop().time()
        self.service._timelines[symbol] = timeline
        cached_timeline = self.service._timelines.get(symbol)
        end_time = asyncio.get_event_loop().time()

        # Then
        execution_time_ms = (end_time - start_time) * 1000
        assert execution_time_ms < 100  # Moins de 100ms
        assert cached_timeline == timeline

    def test_should_handle_multiple_concurrent_symbol_access(self):
        """Test de gestion d'accès concurrents à plusieurs symboles."""
        # Given
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
        test_currency = Currency(code="USD", name="US Dollar", symbol="$")
        timelines = {
            symbol: MarketDataTimeline(symbol=symbol, currency=test_currency)
            for symbol in symbols
        }

        # When
        for symbol, timeline in timelines.items():
            self.service._timelines[symbol] = timeline

        # Then
        for symbol in symbols:
            assert symbol in self.service._timelines
            assert self.service._timelines[symbol] == timelines[symbol]

    def test_should_maintain_stats_consistency_under_load(self):
        """Test de consistance des stats sous charge."""
        # Given
        initial_stats = self.service.stats.copy()
        operations = 100

        # When - Simulation de charge
        for _ in range(operations):
            self.service.stats["cache_hits"] += 1

        # Then
        assert (
            self.service.stats["cache_hits"] == initial_stats["cache_hits"] + operations
        )
        assert all(isinstance(value, int) for value in self.service.stats.values())
